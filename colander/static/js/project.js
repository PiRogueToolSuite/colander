function suggest_entity(input, type) {
    input.on('input', function () {
        $('.suggested-entity').remove()
        const value = input.val();
        if (value.length > 4) {
            $.get(`/entity/${type}/${value}`, function (data) {
                // console.dir(data)
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

$(function () {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))

    handle_comment_controls();

    // $('.martor-preview pre').each(function(i, block){
    //     hljs.highlightBlock(block);
    // });

    $('a, button').click(function (e) {
        const documentation_form = $('#case_documentation_form')
        if (documentation_form !== undefined) {
            console.dir(documentation_form)
            $.ajax({
                async: false,
                type: documentation_form.attr('method'),
                url: documentation_form.attr('action'),
                data: documentation_form.serialize()
            }).done(function (data) {
            }).fail(function (data) {
            });
        }
    })
})
