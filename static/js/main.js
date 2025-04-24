/**
 * Main JavaScript for Meeting to Podcast AI Agent
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(#processing-alert)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // File input validation
    const fileInput = document.getElementById('audioFile');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const fileSize = this.files[0]?.size / 1024 / 1024; // in MB
            const fileType = this.files[0]?.type;
            
            const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/x-m4a'];
            const isValidType = validTypes.includes(fileType);
            
            const errorElement = document.getElementById('file-error');
            if (errorElement) {
                if (fileSize > 100) {
                    errorElement.textContent = 'File size should not exceed 100MB';
                    errorElement.classList.remove('d-none');
                    this.value = '';
                } else if (!isValidType) {
                    errorElement.textContent = 'Please select a valid audio file (MP3, WAV, M4A)';
                    errorElement.classList.remove('d-none');
                    this.value = '';
                } else {
                    errorElement.classList.add('d-none');
                }
            }
        });
    }

    // Handle podcast player controls
    const audioPlayers = document.querySelectorAll('audio');
    audioPlayers.forEach(player => {
        player.addEventListener('play', function() {
            // Pause all other players when one starts playing
            audioPlayers.forEach(otherPlayer => {
                if (otherPlayer !== player && !otherPlayer.paused) {
                    otherPlayer.pause();
                }
            });
        });
    });

    // Refresh podcast list periodically if processing
    let isProcessing = false;
    const processingAlert = document.getElementById('processing-alert');
    
    if (processingAlert && !processingAlert.classList.contains('d-none')) {
        isProcessing = true;
        startPolling();
    }

    function startPolling() {
        if (!isProcessing) return;
        
        const pollInterval = setInterval(() => {
            fetch('/api/podcasts')
                .then(response => response.json())
                .then(data => {
                    // Check if new podcasts have been added
                    const currentCount = document.querySelectorAll('.podcast-card').length;
                    if (data.length > currentCount) {
                        // New podcasts found, reload the page
                        window.location.reload();
                        clearInterval(pollInterval);
                    }
                })
                .catch(error => {
                    console.error('Error polling for podcasts:', error);
                });
        }, 5000); // Poll every 5 seconds
    }
});
