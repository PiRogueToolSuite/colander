export default class FileUpload {
    static DEFAULT_CONFIG = {
        file_input_elem: null,
        upload_uri: '/upload',
        max_chunk_length:  1 * 1024 * 1024,
        success: () => {},
        progress: () => {},
        error: () => {},
        progress_container_elem: null,
    };
    config = {};
    jProgress = null;
    constructor(input_elt_or_config, success_callback, progress_callback, error_callback, upload_url) {
        console.log("constructor", typeof input_elt_or_config, arguments);
        if (typeof input_elt_or_config === 'object') {
            if (input_elt_or_config.file_input_elem) {
                console.log("constructor", "GENERIC Constructor");
                 this._constructor_with_config( input_elt_or_config );
            }
            else if ( $(input_elt_or_config).is('input[type=file]') ) {
                console.log("constructor", "LEGACY Constructor");
                this._constructor_with_config({
                    file_input_elem: input_elt_or_config,
                    upload_uri: upload_url,
                    success: success_callback,
                    progress: progress_callback,
                    error: error_callback
                });
            }
            else {
                throw new Error("Please provide a file input elem or a { config } object");
            }
        }
        else {
            throw new Error("Please provide a file input elem or a { config } object");
        }
    }
    _constructor_with_config(c) {
        this.config = Object.assign( this.config, FileUpload.DEFAULT_CONFIG, c );
        this.next_addr = 0;
        this.slices = {};
    }

    create_progress_bar() {
        this.jProgress = $(
            `<div class="file-details">
                <div class="progress" style="margin-top: 5px;">
                    <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0;">
                    </div>
                </div>
                <span class="file-upload-status text-muted"></span>
            </div>`);
        if (this.config.progress_container_elem) {
            $(this.config.progress_container_elem).empty().append(this.jProgress);
        }
        else {
            let jProgressContainer = $(`<div class="mb-2"></div>`);
            jProgressContainer.append(this.jProgress);
            jProgressContainer.insertAfter($(this.config.file_input_elem));
        }
        //document.getElementById('uploaded_files').innerHTML = progress
    }

    upload() {
        this.validate();
        this.create_progress_bar();
        this.init_file_upload()
            .then(() => {
                console.log("Internal 'upload' success");
            })
            .catch(this.config.error);
    }

    validate() {
        if ( this.config.file_input_elem.files &&
            this.config.file_input_elem.files[0] ) {
            // pass
        }
        else {
            setTimeout(this.config.error.bind(null, 'Please select a file'), 0);
            throw new Error('Please select at least a file');
        }
    }

    handle_upload_initialization(data) {
        this.next_addr = data['next_addr'];
        this.upload_file();
    }

    async init_file_upload() {
        this.file = this.config.file_input_elem.files[0];
        $(this.config.file_input_elem).prop('disabled', true);
        await this.init_file_slices();
        $.ajaxSetup({
            async: true,
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        });
        const payload = {
            'file_name': this.file_name,
            'file_size': this.file_size,
            'chunks': this.slices,
        };
        await $.ajax({
            url: `${this.config.upload_uri}`,
            method: 'POST',
            data: JSON.stringify(payload),
            contentType:'application/json; charset=utf-8',
            dataType: 'json',
            success: (data) => {
                this.upload_request = data;
                this.next_addr = data['next_addr'];
                this.upload_file();
            }
        })
    }

    async init_file_slices () {
        this.file_size = this.file.size;
        this.file_name = this.file.name;
        let addr = 0;
        this.jProgress.find('.file-upload-status').text('Hashing')
        while(addr < this.file_size) {
            let next_chunk = addr + this.config.max_chunk_length + 1 ;
            const chunk = this.file.slice(addr, next_chunk);
            const buf = await chunk.arrayBuffer()
            const bin_hash = await crypto.subtle.digest('SHA-256', buf)
            const hash_array = Array.from(new Uint8Array(bin_hash))
            const hash = hash_array.map(b => b.toString(16).padStart(2, '0')).join('');
            this.slices[addr] = hash;
            addr = next_chunk;
        }
    }

    upload_file() {
        this.jProgress.find('.file-upload-status').text('Uploading')
        let end;
        let start_addr = this.next_addr;
        const formData = new FormData();
        let nextChunk = start_addr + this.config.max_chunk_length + 1;
        let currentChunk = this.file.slice(start_addr, nextChunk);
        let uploadedChunk = start_addr + currentChunk.size
        if (uploadedChunk >= this.file.size) {
            end = 1;
        } else {
            end = 0;
        }
        formData.append('file', currentChunk)
        formData.append('addr', start_addr)
        formData.append('eof', end)
        let percent = 0
        if (this.file.size < this.config.max_chunk_length) {
            percent = Math.round((uploadedChunk / this.file.size) * 100);
        } else {
            percent = Math.round((uploadedChunk / this.file.size) * 100);
        }
        this.jProgress.find('.progress-bar').css('width', percent + '%')
        this.jProgress.find('.progress-bar').text(percent + '%')
        $.ajaxSetup({
            async: true,
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        });
        $.ajax({
            url: `${this.config.upload_uri}/${this.upload_request.id}`,
            type: 'POST',
            dataType: 'json',
            cache: false,
            processData: false,
            contentType: false,
            data: formData,
            error: (xhr) => {
                this.config.error(xhr);
            },
            success: (res) => {
                this.upload_request = res
                this.next_addr = res['next_addr']
                if (this.next_addr > 0) {
                    this.config.progress(this.upload_request, uploadedChunk, this.file.size);
                    // upload file in chunks
                    setTimeout( this.upload_file.bind(this), 0 );
                } else {
                    // upload complete
                    this.jProgress.find('.file-upload-status').text('Success!')
                    this.config.success(this.upload_request);
                }
            }
        });
    };
};
