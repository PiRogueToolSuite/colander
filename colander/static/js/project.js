function suggest_entity(input, type) {
    input.on('input', function () {
        $('.suggested-entity').remove()
        const value = input.val();
        if (value.length > 4) {
            $.get(`/entity/suggest?type=${type}&value=${value}`, function (data) {
                data.forEach(function (d) {
                    const message = `
                        <div class="text-muted mb-0 suggested-entity">
                            Do you mean <a href="${d.url}" class="">${d.text}</a>?
                        </div>
                    `
                    input.after(message)
                })
            })
        }
    })
}

function handle_comment_controls() {
    $('.delete-comment-btn').on('click', function (e) {
        e.preventDefault();
        const self = $(this);
        self.html('<b>Sure?</b>');
        self.removeClass('delete-comment-btn')
        self.unbind('click');
    })
    $('.update-comment-btn').on('click', function () {
        const id = $(this).attr('comment-id');
        $(`.comment-content-${id}`).hide();
        $(`.edit-comment-form-${id}`).show();
    })
    $('.cancel-comment-edit-btn').on('click', function () {
        const id = $(this).attr('comment-id');
        $(`.comment-content-${id}`).show();
        $(`.edit-comment-form-${id}`).hide();
    })
}

function handle_entity_delete_control() {
    $('.delete-entity-btn').on('click', function (e) {
        e.preventDefault();
        const self = $(this);
        self.html('<b>Sure?</b>');
        self.removeClass('delete-entity-btn')
        self.unbind('click');
    })
}

$(function () {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))

    handle_comment_controls();
    handle_entity_delete_control();
})
