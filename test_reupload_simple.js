// Simple test to verify re-upload button functionality
console.log("Testing re-upload button functionality...");

// Check if reuploadBtn exists
const reuploadBtn = document.getElementById('reuploadBtn');
if (reuploadBtn) {
    console.log("✓ reuploadBtn found:", reuploadBtn.textContent.trim());
    
    // Check if event listener is attached
    const clickEvents = getEventListeners(reuploadBtn).click;
    if (clickEvents && clickEvents.length > 0) {
        console.log("✓ Click event listener attached to reuploadBtn");
    } else {
        console.log("✗ No click event listener found on reuploadBtn");
    }
} else {
    console.log("✗ reuploadBtn not found");
}

// Check if handleReupload function exists
if (typeof handleReupload === 'function') {
    console.log("✓ handleReupload function exists");
    
    // Test the function
    try {
        console.log("Testing handleReupload function...");
        handleReupload();
        console.log("✓ handleReupload function executed successfully");
    } catch (error) {
        console.log("✗ Error executing handleReupload:", error.message);
    }
} else {
    console.log("✗ handleReupload function not found");
}

// Helper function to check event listeners (if available)
function getEventListeners(element) {
    if (typeof element.__getEventListeners === 'function') {
        return element.__getEventListeners();
    }
    
    // Fallback for browsers that don't support __getEventListeners
    const listeners = {};
    const events = ['click', 'mouseover', 'mouseout', 'keydown', 'keyup'];
    
    events.forEach(event => {
        const eventListeners = [];
        const eventKey = `on${event}`;
        
        if (typeof element[eventKey] === 'function') {
            eventListeners.push({ listener: element[eventKey] });
        }
        
        if (eventListeners.length > 0) {
            listeners[event] = eventListeners;
        }
    });
    
    return listeners;
}

console.log("Test completed.");
