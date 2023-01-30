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

$(function () {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]')
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl))


})
