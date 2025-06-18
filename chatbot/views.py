from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
import openai
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import ChatSession, ChatMessage, Intent, TrainingPhrase, Response

def get_or_create_session(request):
    if request.user.is_authenticated:
        session, created = ChatSession.objects.get_or_create(
            user=request.user,
            defaults={'session_id': str(uuid.uuid4())}
        )
    else:
        session_id = request.session.get('chat_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['chat_session_id'] = session_id
        
        session, created = ChatSession.objects.get_or_create(
            session_id=session_id
        )
    
    return session

def chatbot_view(request):
    session = get_or_create_session(request)
    messages = ChatMessage.objects.filter(session=session)
    
    context = {
        'session': session,
        'messages': messages,
    }
    return render(request, 'chatbot/chatbot.html', context)

@csrf_exempt
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'error': 'Message is required'}, status=400)
            
            # Get or create chat session
            session = get_or_create_session(request)
            
            # Save user message
            ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=user_message
            )
            
            # Get bot response
            bot_response = get_bot_response(user_message)
            
            # Save bot response
            ChatMessage.objects.create(
                session=session,
                message_type='bot',
                content=bot_response
            )
            
            return JsonResponse({
                'response': bot_response,
                'session_id': session.session_id
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def get_bot_response(user_message):
    # Try to match with intents first
    intent_response = get_intent_response(user_message)
    if intent_response:
        return intent_response
    
    # If no intent match, use OpenAI
    try:
        openai.api_key = 'your-openai-api-key'  # Use environment variable in production
        
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"You are a helpful e-commerce assistant. Answer the following question:\n\nUser: {user_message}\n\nAssistant:",
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        return response.choices[0].text.strip()
    except Exception as e:
        # Fallback response if OpenAI fails
        return "I'm sorry, I'm having trouble understanding. Could you please rephrase your question?"

def get_intent_response(user_message):
    # Get all training phrases
    training_phrases = TrainingPhrase.objects.all()
    
    if not training_phrases.exists():
        return None
    
    # Extract texts and corresponding intents
    texts = [phrase.text for phrase in training_phrases]
    intents = [phrase.intent for phrase in training_phrases]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)
    
    # Transform user message
    user_vector = vectorizer.transform([user_message])
    
    # Calculate similarity
    similarities = cosine_similarity(user_vector, tfidf_matrix)[0]
    
    # Find best match
    best_match_index = np.argmax(similarities)
    best_match_score = similarities[best_match_index]
    
    # If similarity is above threshold, return response
    if best_match_score > 0.5:
        intent = intents[best_match_index]
        responses = Response.objects.filter(intent=intent)
        
        if responses.exists():
            # Return random response for the intent
            import random
            return random.choice(responses).text
    
    return None

def chatbot_widget(request):
    return render(request, 'chatbot/widget.html')