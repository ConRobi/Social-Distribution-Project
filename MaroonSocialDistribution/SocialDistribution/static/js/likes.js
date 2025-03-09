document.addEventListener('DOMContentLoaded', function() {
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
    // Handle like for comments
    document.querySelectorAll('.like-comment-button').forEach(button => {
      button.addEventListener('click', function() {
        // Get the comment UUID
        const commentUuid = this.getAttribute('data-comment-uuid');
  
        fetch(`/comment/${commentUuid}/like_comment/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
          },
        })
        .then(response => response.json())
        .then(data => {
        // Update likes count for display
          document.getElementById('comment-likes-count-' + commentUuid).textContent = data.likes_count;
        });
      });
    });
  });
