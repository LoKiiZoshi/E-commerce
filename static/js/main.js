// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Chatbot functionality
    const chatbotToggle = document.getElementById('chatbotToggle');
    const chatbotWidget = document.getElementById('chatbotWidget');
    const closeChatbot = document.getElementById('closeChatbot');
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (chatbotToggle && chatbotWidget && closeChatbot && chatbotForm && chatbotInput && chatMessages) {
        // Toggle chatbot visibility
        chatbotToggle.addEventListener('click', function() {
            chatbotWidget.style.display = 'flex';
            chatbotToggle.style.display = 'none';
        });
        
        // Close chatbot
        closeChatbot.addEventListener('click', function() {
            chatbotWidget.style.display = 'none';
            chatbotToggle.style.display = 'flex';
        });
        
        // Handle chatbot form submission
        chatbotForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatbotInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage('user', message);
            
            // Clear input
            chatbotInput.value = '';
            
            // Send message to backend
            sendChatMessage(message);
        });
        
        // Function to add message to chat
        function addMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(contentDiv);
            chatMessages.appendChild(messageDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // Function to send message to backend
        function sendChatMessage(message) {
            // Show typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot-message typing';
            typingDiv.innerHTML = '<div class="message-content">Typing...</div>';
            chatMessages.appendChild(typingDiv);
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Send AJAX request to backend
            fetch('/chatbot/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);
                
                // Add bot response
                addMessage('bot', data.response);
            })
            .catch(error => {
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);
                
                // Add error message
                addMessage('bot', 'Sorry, I encountered an error. Please try again later.');
                console.error('Error:', error);
            });
        }
    }
    
    // Add to cart functionality
    const addToCartForms = document.querySelectorAll('.add-to-cart-form');
    
    addToCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const productId = form.getAttribute('data-product-id');
            
            // Send AJAX request to add to cart
            fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update cart count
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_total;
                    }
                    
                    // Show success message
                    showToast('Success', data.message, 'success');
                } else {
                    showToast('Error', data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error', 'An error occurred. Please try again.', 'danger');
                console.error('Error:', error);
            });
        });
    });
    
    // Update cart functionality
    const updateCartForms = document.querySelectorAll('.update-cart-form');
    
    updateCartForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const itemId = form.getAttribute('data-item-id');
            
            // Send AJAX request to update cart
            fetch(`/cart/update/${itemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update cart count
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_total;
                    }
                    
                    // Update item total
                    const itemTotal = document.querySelector(`.item-total-${itemId}`);
                    if (itemTotal) {
                        itemTotal.textContent = formatCurrency(data.item_total);
                    }
                    
                    // Update cart subtotal
                    const cartSubtotal = document.querySelector('.cart-subtotal');
                    if (cartSubtotal) {
                        cartSubtotal.textContent = formatCurrency(data.cart_subtotal);
                    }
                    
                    // Show success message
                    showToast('Success', 'Cart updated successfully.', 'success');
                } else {
                    showToast('Error', data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error', 'An error occurred. Please try again.', 'danger');
                console.error('Error:', error);
            });
        });
    });
    
    // Remove from cart functionality
    const removeFromCartButtons = document.querySelectorAll('.remove-from-cart');
    
    removeFromCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const itemId = button.getAttribute('data-item-id');
            
            // Send AJAX request to remove from cart
            fetch(`/cart/remove/${itemId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update cart count
                    const cartCount = document.querySelector('.cart-count');
                    if (cartCount) {
                        cartCount.textContent = data.cart_total;
                    }
                    
                    // Remove item from DOM
                    const cartItem = document.querySelector(`.cart-item-${itemId}`);
                    if (cartItem) {
                        cartItem.remove();
                    }
                    
                    // Update cart subtotal
                    const cartSubtotal = document.querySelector('.cart-subtotal');
                    if (cartSubtotal) {
                        cartSubtotal.textContent = formatCurrency(data.cart_subtotal);
                    }
                    
                    // Show success message
                    showToast('Success', data.message, 'success');
                    
                    // If cart is empty, reload page
                    if (data.cart_total === 0) {
                        window.location.reload();
                    }
                } else {
                    showToast('Error', data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error', 'An error occurred. Please try again.', 'danger');
                console.error('Error:', error);
            });
        });
    });
    
    // Product image gallery
    const productThumbnails = document.querySelectorAll('.product-thumbnail');
    const productMainImage = document.querySelector('.product-main-image');
    
    if (productThumbnails.length > 0 && productMainImage) {
        productThumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                // Remove active class from all thumbnails
                productThumbnails.forEach(thumb => {
                    thumb.classList.remove('active');
                });
                
                // Add active class to clicked thumbnail
                thumbnail.classList.add('active');
                
                // Update main image
                const imageUrl = thumbnail.getAttribute('data-image-url');
                productMainImage.src = imageUrl;
            });
        });
    }
    
    // Review voting functionality
    const reviewVoteButtons = document.querySelectorAll('.review-vote');
    
    reviewVoteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const reviewId = button.getAttribute('data-review-id');
            const voteType = button.getAttribute('data-vote-type');
            
            // Send AJAX request to vote
            fetch(`/reviews/vote/${reviewId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `vote=${voteType}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update vote counts
                    const helpfulCount = document.querySelector(`.helpful-count-${reviewId}`);
                    const notHelpfulCount = document.querySelector(`.not-helpful-count-${reviewId}`);
                    
                    if (helpfulCount) {
                        helpfulCount.textContent = data.helpful_count;
                    }
                    
                    if (notHelpfulCount) {
                        notHelpfulCount.textContent = data.not_helpful_count;
                    }
                    
                    // Update button states
                    const helpfulButton = document.querySelector(`.review-vote[data-review-id="${reviewId}"][data-vote-type="helpful"]`);
                    const notHelpfulButton = document.querySelector(`.review-vote[data-review-id="${reviewId}"][data-vote-type="not_helpful"]`);
                    
                    if (data.action === 'added') {
                        if (voteType === 'helpful' && helpfulButton) {
                            helpfulButton.classList.add('active');
                        } else if (voteType === 'not_helpful' && notHelpfulButton) {
                            notHelpfulButton.classList.add('active');
                        }
                    } else if (data.action === 'removed') {
                        if (voteType === 'helpful' && helpfulButton) {
                            helpfulButton.classList.remove('active');
                        } else if (voteType === 'not_helpful' && notHelpfulButton) {
                            notHelpfulButton.classList.remove('active');
                        }
                    } else if (data.action === 'changed') {
                        if (voteType === 'helpful') {
                            helpfulButton.classList.add('active');
                            notHelpfulButton.classList.remove('active');
                        } else {
                            helpfulButton.classList.remove('active');
                            notHelpfulButton.classList.add('active');
                        }
                    }
                } else {
                    showToast('Error', data.error, 'danger');
                }
            })
            .catch(error => {
                showToast('Error', 'An error occurred. Please try again.', 'danger');
                console.error('Error:', error);
            });
        });
    });
    
    // Face recognition login
    const faceLoginButton = document.getElementById('faceLoginButton');
    const faceLoginModal = document.getElementById('faceLoginModal');
    const faceLoginVideo = document.getElementById('faceLoginVideo');
    const faceLoginCanvas = document.getElementById('faceLoginCanvas');
    const faceLoginStatus = document.getElementById('faceLoginStatus');
    
    if (faceLoginButton && faceLoginModal && faceLoginVideo && faceLoginCanvas && faceLoginStatus) {
        // Initialize face-api.js
        Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('/static/models/face-api'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/static/models/face-api'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/static/models/face-api')
        ]).then(startFaceLogin);
        
        function startFaceLogin() {
            faceLoginButton.addEventListener('click', function() {
                // Show modal
                const modal = new bootstrap.Modal(faceLoginModal);
                modal.show();
                
                // Start video
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(stream => {
                        faceLoginVideo.srcObject = stream;
                    })
                    .catch(err => {
                        faceLoginStatus.textContent = 'Error accessing camera: ' + err.message;
                        faceLoginStatus.classList.add('text-danger');
                    });
                
                // When video is playing, start face detection
                faceLoginVideo.addEventListener('play', () => {
                    // Set canvas dimensions
                    const displaySize = { width: faceLoginVideo.width, height: faceLoginVideo.height };
                    faceapi.matchDimensions(faceLoginCanvas, displaySize);
                    
                    // Detect face every 100ms
                    const interval = setInterval(async () => {
                        const detections = await faceapi.detectAllFaces(faceLoginVideo, new faceapi.TinyFaceDetectorOptions())
                            .withFaceLandmarks()
                            .withFaceDescriptors();
                        
                        // Draw detections
                        const resizedDetections = faceapi.resizeResults(detections, displaySize);
                        faceLoginCanvas.getContext('2d').clearRect(0, 0, faceLoginCanvas.width, faceLoginCanvas.height);
                        faceapi.draw.drawDetections(faceLoginCanvas, resizedDetections);
                        faceapi.draw.drawFaceLandmarks(faceLoginCanvas, resizedDetections);
                        
                        // If face detected, capture and send to backend
                        if (detections.length > 0) {
                            clearInterval(interval);
                            
                            // Stop video
                            const stream = faceLoginVideo.srcObject;
                            const tracks = stream.getTracks();
                            tracks.forEach(track => track.stop());
                            
                            // Capture face data
                            const faceData = captureImage(faceLoginVideo);
                            
                            // Update status
                            faceLoginStatus.textContent = 'Face detected! Authenticating...';
                            faceLoginStatus.classList.remove('text-danger');
                            faceLoginStatus.classList.add('text-info');
                            
                            // Send to backend
                            sendFaceData(faceData);
                        }
                    }, 100);
                    
                    // When modal is hidden, stop video
                    faceLoginModal.addEventListener('hidden.bs.modal', () => {
                        clearInterval(interval);
                        
                        if (faceLoginVideo.srcObject) {
                            const stream = faceLoginVideo.srcObject;
                            const tracks = stream.getTracks();
                            tracks.forEach(track => track.stop());
                        }
                    });
                });
            });
        }
        
        function captureImage(video) {
            const canvas = document.createElement('canvas');
            canvas.width = video.width;
            canvas.height = video.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/jpeg');
        }
        
        function sendFaceData(faceData) {
            fetch('/users/face-login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    face_data: faceData
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    faceLoginStatus.textContent = data.message;
                    faceLoginStatus.classList.remove('text-info', 'text-danger');
                    faceLoginStatus.classList.add('text-success');
                    
                    // Redirect to home page after successful login
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                } else {
                    faceLoginStatus.textContent = data.message;
                    faceLoginStatus.classList.remove('text-info', 'text-success');
                    faceLoginStatus.classList.add('text-danger');
                }
            })
            .catch(error => {
                faceLoginStatus.textContent = 'Error: ' + error.message;
                faceLoginStatus.classList.remove('text-info', 'text-success');
                faceLoginStatus.classList.add('text-danger');
                console.error('Error:', error);
            });
        }
    }
    
    // Register face functionality
    const registerFaceButton = document.getElementById('registerFaceButton');
    const registerFaceModal = document.getElementById('registerFaceModal');
    const registerFaceVideo = document.getElementById('registerFaceVideo');
    const registerFaceCanvas = document.getElementById('registerFaceCanvas');
    const registerFaceStatus = document.getElementById('registerFaceStatus');
    
    if (registerFaceButton && registerFaceModal && registerFaceVideo && registerFaceCanvas && registerFaceStatus) {
        // Initialize face-api.js
        Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('/static/models/face-api'),
            faceapi.nets.faceLandmark68Net.loadFromUri('/static/models/face-api'),
            faceapi.nets.faceRecognitionNet.loadFromUri('/static/models/face-api')
        ]).then(startRegisterFace);
        
        function startRegisterFace() {
            registerFaceButton.addEventListener('click', function() {
                // Show modal
                const modal = new bootstrap.Modal(registerFaceModal);
                modal.show();
                
                // Start video
                navigator.mediaDevices.getUserMedia({ video: true })
                    .then(stream => {
                        registerFaceVideo.srcObject = stream;
                    })
                    .catch(err => {
                        registerFaceStatus.textContent = 'Error accessing camera: ' + err.message;
                        registerFaceStatus.classList.add('text-danger');
                    });
                
                // When video is playing, start face detection
                registerFaceVideo.addEventListener('play', () => {
                    // Set canvas dimensions
                    const displaySize = { width: registerFaceVideo.width, height: registerFaceVideo.height };
                    faceapi.matchDimensions(registerFaceCanvas, displaySize);
                    
                    // Detect face every 100ms
                    const interval = setInterval(async () => {
                        const detections = await faceapi.detectAllFaces(registerFaceVideo, new faceapi.TinyFaceDetectorOptions())
                            .withFaceLandmarks()
                            .withFaceDescriptors();
                        
                        // Draw detections
                        const resizedDetections = faceapi.resizeResults(detections, displaySize);
                        registerFaceCanvas.getContext('2d').clearRect(0, 0, registerFaceCanvas.width, registerFaceCanvas.height);
                        faceapi.draw.drawDetections(registerFaceCanvas, resizedDetections);
                        faceapi.draw.drawFaceLandmarks(registerFaceCanvas, resizedDetections);
                        
                        // If face detected, capture and send to backend
                        if (detections.length > 0) {
                            clearInterval(interval);
                            
                            // Stop video
                            const stream = registerFaceVideo.srcObject;
                            const tracks = stream.getTracks();
                            tracks.forEach(track => track.stop());
                            
                            // Capture face data
                            const faceData = captureImage(registerFaceVideo);
                            
                            // Update status
                            registerFaceStatus.textContent = 'Face detected! Registering...';
                            registerFaceStatus.classList.remove('text-danger');
                            registerFaceStatus.classList.add('text-info');
                            
                            // Send to backend
                            sendRegisterFaceData(faceData);
                        }
                    }, 100);
                    
                    // When modal is hidden, stop video
                    registerFaceModal.addEventListener('hidden.bs.modal', () => {
                        clearInterval(interval);
                        
                        if (registerFaceVideo.srcObject) {
                            const stream = registerFaceVideo.srcObject;
                            const tracks = stream.getTracks();
                            tracks.forEach(track => track.stop());
                        }
                    });
                });
            });
        }
        
        function captureImage(video) {
            const canvas = document.createElement('canvas');
            canvas.width = video.width;
            canvas.height = video.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL('image/jpeg');
        }
        
        function sendRegisterFaceData(faceData) {
            fetch('/users/register-face/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    face_data: faceData
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    registerFaceStatus.textContent = data.message;
                    registerFaceStatus.classList.remove('text-info', 'text-danger');
                    registerFaceStatus.classList.add('text-success');
                } else {
                    registerFaceStatus.textContent = data.message;
                    registerFaceStatus.classList.remove('text-info', 'text-success');
                    registerFaceStatus.classList.add('text-danger');
                }
            })
            .catch(error => {
                registerFaceStatus.textContent = 'Error: ' + error.message;
                registerFaceStatus.classList.remove('text-info', 'text-success');
                registerFaceStatus.classList.add('text-danger');
                console.error('Error:', error);
            });
        }
    }
    
    // Helper functions
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
    
    function showToast(title, message, type) {
        const toastContainer = document.getElementById('toastContainer');
        
        if (!toastContainer) {
            // Create toast container if it doesn't exist
            const container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        // Create toast content
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong>: ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        // Add toast to container
        document.getElementById('toastContainer').appendChild(toast);
        
        // Initialize and show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
});