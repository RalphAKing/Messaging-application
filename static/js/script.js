function vote(postId, direction) {
    fetch(`/vote/${postId}/${direction}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update score
                document.getElementById(`score-${postId}`).textContent = data.newScore;
                
                // Update button styles
                const upvoteBtn = document.getElementById(`upvote-${postId}`);
                const downvoteBtn = document.getElementById(`downvote-${postId}`);
                
                if (direction === 'up') {
                    if (upvoteBtn.classList.contains('voted')) {
                        upvoteBtn.classList.remove('voted');
                    } else {
                        upvoteBtn.classList.add('voted');
                        downvoteBtn.classList.remove('voted');
                    }
                } else {
                    if (downvoteBtn.classList.contains('voted')) {
                        downvoteBtn.classList.remove('voted');
                    } else {
                        downvoteBtn.classList.add('voted');
                        upvoteBtn.classList.remove('voted');
                    }
                }
            }
        });
}


function toggleComments(commentId) {
    const commentSection = document.querySelector(`#comments-${commentId}`);
    commentSection.classList.toggle('hidden');
}

function goBack() {
    window.history.back();
}
