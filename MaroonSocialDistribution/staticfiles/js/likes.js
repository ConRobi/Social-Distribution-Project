document.addEventListener('DOMContentLoaded', function() {
    // Assuming all like buttons have a class like 'like-button'
    document.querySelectorAll('.like-post-button').forEach(button => {
        button.addEventListener('click', function() {
            // Get the post ID
            const postId = this.getAttribute('data-post-id');  

            // Send the like request (using fetch)
            fetch(`/post/${postId}/like_post/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
            })
            .then(response => response.json())
            .then(data => {
                // Update the likes count
                document.getElementById('post-likes-count-' + postId).textContent = data.likes_count;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while liking the post.');
            });
        });
    });
    // TODO add functionality for comments when comment model made
    // // Handle like/unlike for comments
    // document.querySelectorAll('.like-comment-button').forEach(button => {
    //   button.addEventListener('click', function() {
    //     var commentId = this.getAttribute('data-comment-id');
    //     var action = this.textContent.trim() === "Unlike" ? "unlike_comment" : "like_comment";  // Check if it's currently liked
  
    //     fetch(`/comment/${commentId}/${action}/`, {
    //       method: 'POST',
    //       headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
    //       },
    //     })
    //     .then(response => response.json())
    //     .then(data => {
    //       document.getElementById('comment-likes-count-' + commentId).textContent = data.likes_count;
    //       this.textContent = action === "like_comment" ? "Unlike" : "Like";
    //     });
    //   });
    // });
  });
