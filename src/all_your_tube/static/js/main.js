// All Your Tube - Main JavaScript functionality

let eventSource = null;
let autoScroll = true;
let currentPid = null;
let downloadCompleted = false;

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
    initializeFormValidation();
    initializeLogControls();
    initializeFormSubmission();
});

function initializeFormValidation() {
    const forms = document.getElementsByClassName('needs-validation');
    Array.prototype.filter.call(forms, function (form) {
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            event.stopPropagation();

            if (form.checkValidity() === true) {
                submitDownloadForm();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

function initializeLogControls() {
    const logs = document.getElementById('logs');
    const output = document.getElementById('output');
    const desc = document.getElementById('desc');
    const toggleBtn = document.getElementById('toggleAutoScroll');
    const scrollTopBtn = document.getElementById('scrollToTop');
    const scrollBottomBtn = document.getElementById('scrollToBottom');

    let isUserScrolling = false;
    let hasNewContent = false;

    // Scroll detection for existing log.css behavior
    logs.addEventListener('scroll', function () {
        isUserScrolling = true;
        var isAtBottom = (logs.scrollTop + logs.offsetHeight) >= (logs.scrollHeight - 50);

        if (isAtBottom) {
            hasNewContent = false;
        }

        setTimeout(function () {
            isUserScrolling = false;
        }, 1000);
    });

    // Auto-scroll toggle (using pixel art styling)
    toggleBtn.addEventListener('click', function () {
        autoScroll = !autoScroll;
        if (autoScroll) {
            toggleBtn.innerHTML = '▲ AUTO-SCROLL ON ▲';
            toggleBtn.style.background = '#449d44';
            toggleBtn.style.boxShadow = 'inset 2px 2px 0px #2d6a2d, 3px 3px 0px #000';
        } else {
            toggleBtn.innerHTML = '▼ AUTO-SCROLL OFF ▼';
            toggleBtn.style.background = '#5cb85c';
            toggleBtn.style.boxShadow = '3px 3px 0px #000';
        }

        if (autoScroll && hasNewContent) {
            scrollToBottomSmooth();
        }
    });

    // Scroll to top button
    scrollTopBtn.addEventListener('click', function () {
        logs.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        hasNewContent = false;
    });

    // Scroll to bottom button
    scrollBottomBtn.addEventListener('click', scrollToBottomSmooth);

    // Hide logging section
    document.getElementById('hideLogging').addEventListener('click', function () {
        hideLoggingSection();
    });


    function scrollToBottomSmooth() {
        logs.scrollTo({
            top: logs.scrollHeight,
            behavior: 'smooth'
        });
        hasNewContent = false;
    }

    // Store references for use in other functions
    window.logElements = {
        logs: logs,
        output: output,
        desc: desc,
        isUserScrolling: () => isUserScrolling,
        hasNewContent: hasNewContent,
        setHasNewContent: (value) => { hasNewContent = value; },
    };
}

function initializeFormSubmission() {
    // Handle form submission via AJAX
    document.getElementById('downloadForm').addEventListener('submit', function (e) {
        e.preventDefault();
        submitDownloadForm();
    });
}

function submitDownloadForm() {
    const form = document.getElementById('downloadForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;

    // Show loading state
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';

    // Prepare form data
    const formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showLoggingSection();
                startLogStreaming(data.pid, data.subdir);
                updateConnectionStatus('connected', 'Connected');
                setSubmitButtonRunning();
            } else {
                showError(data.error || 'Download failed to start');
                updateConnectionStatus('error', 'Error');
                // Reset button on error
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('Network error occurred');
            updateConnectionStatus('error', 'Connection Error');
            // Reset button only on error
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        });
}

function showLoggingSection() {
    const section = document.getElementById('loggingSection');
    section.style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth' });
}

function hideLoggingSection() {
    document.getElementById('loggingSection').style.display = 'none';
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
}

function startLogStreaming(pid, subdir) {
    currentPid = pid;
    downloadCompleted = false; // Reset completion flag

    // Close existing connection
    if (eventSource) {
        eventSource.close();
    }

    // Build stream URL - Note: URL_PREFIX will need to be passed from template
    const urlPrefix = window.URL_PREFIX || '';
    const streamUrl = `${urlPrefix}/stream/${pid}?subdir=${subdir}`;

    // Create new EventSource
    eventSource = new EventSource(streamUrl);

    eventSource.onopen = function () {
        updateConnectionStatus('connected', '● Connected');
    };

    eventSource.onerror = function (error) {
        console.log('EventSource error:', error);

        // Only show error and attempt reconnect if the readyState indicates a real error
        if (eventSource.readyState === EventSource.CLOSED) {
            updateConnectionStatus('error', '● Connection Lost');

            // Only attempt to reconnect if we still have an active PID and haven't completed
            if (currentPid) {
                setTimeout(() => {
                    updateConnectionStatus('connecting', '● Reconnecting...');
                    startLogStreaming(currentPid, subdir);
                }, 5000);
            }
        } else if (eventSource.readyState === EventSource.CONNECTING) {
            updateConnectionStatus('connecting', '● Reconnecting...');
        }
    };

    eventSource.onmessage = function (event) {
        const logs = window.logElements.logs;
        const output = window.logElements.output;
        const desc = window.logElements.desc;

        // Check if user is at bottom before adding content (existing log.css behavior)
        var wasAtBottom = (logs.scrollTop + logs.offsetHeight) >= (logs.scrollHeight - 10);

        output.textContent += "\n" + event.data;

        // Auto-scroll if enabled, user isn't scrolling (existing log.css behavior)
        if (autoScroll && !window.logElements.isUserScrolling()) {
            logs.scrollTop = logs.scrollHeight;
        } else if (!wasAtBottom) {
            // Show new content indicator if user has scrolled up
            window.logElements.setHasNewContent(true);
        }

        // Update description (existing log.css behavior)
        if (!event.data.includes("[download] Sleeping")) {
            desc.textContent = "Status: " + event.data;
        }

        // Handle completion (existing log.css behavior)
        if (!downloadCompleted && (event.data == "Download Complete" || event.data == "---^-^---" ||
            event.data.includes("has already been downloaded"))) {
            downloadCompleted = true; // Prevent multiple completion triggers
            updateConnectionStatus('connected', '● Complete');
            resetSubmitButton();

            // Delay closing the stream to capture any final messages
            setTimeout(() => {
                if (eventSource) {
                    eventSource.close();
                    eventSource = null;
                    currentPid = null;
                }
            }, 5000); // Wait 5 seconds before closing to catch all final messages
        }
    };
}

function setSubmitButtonRunning() {
    const submitButton = document.querySelector('#downloadForm button[type="submit"]');
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running...';
    submitButton.disabled = false; // Allow form to be submitted again if needed
}

function resetSubmitButton() {
    const submitButton = document.querySelector('#downloadForm button[type="submit"]');
    submitButton.innerHTML = '<i class="fas fa-download me-2"></i>Start Download';
    submitButton.disabled = false;
}

function showLoggingSection() {
    const section = document.getElementById('loggingSection');
    const desc = document.getElementById('desc');

    section.style.display = 'block';
    desc.textContent = "Status: Starting...";
    section.scrollIntoView({ behavior: 'smooth' });
}

function updateConnectionStatus(status, text) {
    const statusElement = document.getElementById('connectionStatus');
    statusElement.style.fontFamily = "'Courier New', monospace";
    statusElement.style.fontSize = '12px';
    statusElement.style.fontWeight = 'bold';
    statusElement.style.padding = '4px 8px';
    statusElement.style.border = '2px solid #000';

    switch (status) {
        case 'connected':
            statusElement.style.background = '#00ff00';
            statusElement.style.color = '#000';
            statusElement.innerHTML = '● ' + text.toUpperCase();
            break;
        case 'error':
            statusElement.style.background = '#ff0000';
            statusElement.style.color = '#fff';
            statusElement.innerHTML = '✖ ERROR';
            break;
        case 'connecting':
            statusElement.style.background = '#ffff00';
            statusElement.style.color = '#000';
            statusElement.innerHTML = '◐ CONNECTING...';
            break;
        default:
            statusElement.style.background = '#cccccc';
            statusElement.style.color = '#000';
            statusElement.innerHTML = '● READY';
            break;
    }
}

function showError(message) {
    // Create and show error alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>Error:</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const form = document.getElementById('downloadForm');
    form.parentNode.insertBefore(alertDiv, form.nextSibling);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function () {
    if (eventSource) {
        eventSource.close();
    }
});
