function vote(postId, direction) {
    fetch(`/vote/${postId}/${direction}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
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
