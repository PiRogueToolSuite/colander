export default class FileUpload {

  static State = Object.freeze({
    VALIDATING: Symbol('initialization'),
    VALIDATED: Symbol('validated'),
    INITIALIZING: Symbol('initialization'),
    HASHING: Symbol('hashing'),
    HASHED: Symbol('hashed'),
    INITIALIZED: Symbol('initialized'),
    UPLOADING: Symbol('uploading'),
    UPLOADED: Symbol('uploaded'),
    ERROR: Symbol('error'),
  });

  static DEFAULT_CONFIG = {
    csrf_token: null,
    file_input_elem: null,
    upload_uri: '/upload',
    max_chunk_length:  1 * 1024 * 1024,
    success: () => {},
    progress: () => {},
    error: () => {},
  };

  config = {};

  /**
   * Construct a FileUpload uploader.
   * Can be called with inline parameters or config object directly as first parameter.
   * config: {
   *   success: Function({UploadRequest}),
   *   progress: Function(FileUpload.State, {UploadRequest}, current_bytes, total_bytes),
   *   error: Function(Error),
   *   upload_uri: String,
   *   csrf_token: String,
   * }
   * @param success_callback_or_config
   * @param progress_callback
   * @param error_callback
   * @param upload_uri
   * @param csrf_token
   */
  constructor(success_callback_or_config, progress_callback, error_callback, upload_uri, csrf_token) {
    if (typeof success_callback_or_config === 'function') {
      this._constructor_with_config({
        csrf_token: csrf_token,
        upload_uri: upload_uri,
        success: success_callback_or_config,
        progress: progress_callback,
        error: error_callback
      });
    }
    else {
      this._constructor_with_config( success_callback_or_config );
    }
  }

  _constructor_with_config(c) {
    this.config = Object.assign( this.config, FileUpload.DEFAULT_CONFIG, c );
    this.next_addr = 0;
    this.slices = {};
  }

  upload(fileToUpload) {
    this.validate(fileToUpload)
      .then(this.init_file_upload.bind(this))
      .then(() => {
        // Upload started successfully
        // Nothing to do
      })
      .catch((err) => {
        this.config.progress(FileUpload.State.ERROR);
        this.config.error(err);
      });
  }

  async validate(fileToUpload) {
    console.log('file ?', fileToUpload);
    this.config.progress(FileUpload.State.VALIDATING);
    if ( fileToUpload ) {
      // pass
    }
    else {
      throw new Error('Please select a file');
    }
    this.config.progress(FileUpload.State.VALIDATED);
    return fileToUpload;
  }

  async init_file_upload(fileToUpload) {
    this.config.progress(FileUpload.State.INITIALIZING);

    this.file = fileToUpload;

    await this.init_file_slices();

    $.ajaxSetup({
      async: true,
      headers: {
        "X-CSRFToken": this.config.csrf_token,
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
        this.config.progress(FileUpload.State.INITIALIZED);
        this.upload_request = data;
        this.next_addr = data['next_addr'];
        this.upload_file();
      }
    });
  }

  async init_file_slices() {
    this.config.progress(FileUpload.State.HASHING);

    this.file_size = this.file.size;
    this.file_name = this.file.name;
    let addr = 0;

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

    this.config.progress(FileUpload.State.HASHED);
  }

  upload_file() {
    let end;
    let start_addr = this.next_addr;
    const formData = new FormData();
    let nextChunk = start_addr + this.config.max_chunk_length + 1;
    let currentChunk = this.file.slice(start_addr, nextChunk);
    let uploadedChunk = start_addr + currentChunk.size;
    if (uploadedChunk >= this.file.size) {
      end = 1;
    } else {
      end = 0;
    }

    formData.append('file', currentChunk);
    formData.append('addr', start_addr);
    formData.append('eof', end);

    this.config.progress(FileUpload.State.UPLOADING, this.upload_request, uploadedChunk, this.file.size);

    $.ajaxSetup({
      async: true,
      headers: {
        "X-CSRFToken": this.config.csrf_token,
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
        this.config.progress(FileUpload.State.ERROR);
        this.config.error(xhr);
      },
      success: (res) => {
        this.upload_request = res;
        this.next_addr = res['next_addr'];
        if (this.next_addr > 0) {
          // next chunk file upload
          setTimeout( this.upload_file.bind(this), 0 );
        } else {
          // upload complete
          this.config.progress(FileUpload.State.UPLOADED);
          this.config.success(this.upload_request);
        }
      },
    });
  };
};
