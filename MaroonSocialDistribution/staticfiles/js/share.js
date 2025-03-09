document.addEventListener("DOMContentLoaded", function () {
    const shareButton = document.getElementById("share-post-button");
    
    if (shareButton) {
        shareButton.addEventListener("click", async function () {
            const postUrl = document.getElementById("post-url").value; // Get post URL

            try {
                // ✅ Use Clipboard API for modern browsers
                await navigator.clipboard.writeText(postUrl);
                showShareMessage("Link copied!");
            } catch (err) {
                console.error("Clipboard API failed, using fallback:", err);
                fallbackCopy(postUrl);
            }
        });
    }

    // ✅ Fallback method for older browsers
    function fallbackCopy(text) {
        const tempInput = document.createElement("textarea"); // Use textarea to allow long URLs
        tempInput.value = text;
        document.body.appendChild(tempInput);
        tempInput.select();
        document.execCommand("copy"); // Copy to clipboard
        document.body.removeChild(tempInput);
        showShareMessage("Link copied!");
    }

    // ✅ Show confirmation message
    function showShareMessage(message) {
        const shareMessage = document.getElementById("share-message");
        shareMessage.textContent = message;
        shareMessage.style.display = "inline";
        setTimeout(() => {
            shareMessage.style.display = "none";
        }, 2000);
    }
});
