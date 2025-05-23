function suggest_entity(input, type, csrf, cid) {
    let case_id = cid || null;
    input.on('input', function () {
        $('.suggested-entity').remove()
        const value = input.val();
        if (value.length > 4) {
            $.ajax({
                type: 'POST',
                url: '/rest/entity/suggest',
                dataType: 'json',
                data: {
                    type: type,
                    value: value,
                    case_id: case_id,
                },
                headers: {
                    'X-CSRFToken': csrf,
                },
                success: function (data) {
                    data.forEach(function (d) {
                        const message = `
                        <div class="text-muted mb-0 suggested-entity">
                            Do you mean <a href="${d.url}" class="">${d.text}</a>?
                        </div>
                    `
                        input.after(message)
                    })
                }
            });
        }
    })
}

function handle_comment_controls() {
  /* Now handled by ConfirmButton.vues
    $('.delete-comment-btn').on('click', function (e) {
        e.preventDefault();
        const self = $(this);
        self.html('<b>Sure?</b>');
        self.removeClass('delete-comment-btn')
        self.unbind('click');
    })
  */
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

function handle_pin_toggler_buttons() {
  $('button.pin-toggle').click(function(e){
    let href = $(this).attr('data-href');
    if (href) {
      window.open(href, '_self');
    }
    e.preventDefault();
    e.stopPropagation();
    return false;
  });
}

export default () => {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => {
        let opts = {
            html: true
        }
        if (popoverTriggerEl.hasAttribute('data-bs-content-id')) {
            opts.content = document.getElementById(popoverTriggerEl.getAttribute('data-bs-content-id')).innerHTML;
        }
        new bootstrap.Popover(popoverTriggerEl, opts)
    })

    // Enable tabs
    $('#tabs-menu a').on('click', function (e) {
        e.preventDefault()
        $(this).tab('show')
    })

    handle_comment_controls();
    handle_pin_toggler_buttons();
};
