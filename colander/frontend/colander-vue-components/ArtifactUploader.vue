<script>

import FileUpload from './legacy/file_upload';

function register_legacy_uploader(case_id, csrf_token) {

  if ( $('#id_upload_request_ref').val()?.trim() ) {
      $('#upload_btn').prop('disabled', true);
      $('#upload_btn').hide();
      return;
  }
  $('#upload_submit_btn').prop('disabled', true);
  $('#upload_submit_btn').hide();

  function upload_success(data) {
    $('#artifact-upload-form .disableable').prop('disabled', false);
    $('#id_upload_request_ref').val(data.id);
    $('#id_file').prop('disabled', true);
    $('#upload_btn').prop('disabled', true);
    $('#upload_btn').hide();
    $('#upload_submit_btn').prop('disabled', false);
    $('#upload_submit_btn').show();

    $('#artifact-upload-form').submit();
  }

  function upload_error(err) {
    $('#id_file').prop('disabled', false);
    $('#artifact-upload-form .disableable').prop('disabled', false);
    $('#upload_btn').prop('disabled', false);

    if (err instanceof Error) {
      alert(err.message);
    }
    else if (typeof err === 'string') {
      alert(err);
    }
    else {
      alert('Unable to upload your file. Please refresh this page and contact your administrator.');
    }
  }

  let jProgress = null;
  function create_progress_bar() {
    jProgress = $(
      `<div class="file-details">
          <div class="progress" style="margin-top: 5px;">
              <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0;">
              </div>
          </div>
          <span class="file-upload-status text-muted"></span>
      </div>`);
    let jProgressContainer = $(`<div class="mb-2"></div>`);
    jProgressContainer.append(jProgress);
    jProgressContainer.insertAfter($('#id_file'));
  }

  function upload_progress(state, data, sent, total) {
    if (state === FileUpload.State.VALIDATED) {
      console.log('Validated ...');
      $('#id_file').prop('disabled', true);
    }
    if (state === FileUpload.State.INITIALIZING) {
      console.log('Initializing ...');
      create_progress_bar();
    }
    if (state === FileUpload.State.HASHING) {
      console.log('Hashing ...');
      jProgress.find('.file-upload-status').text('Hashing');
    }
    if (state === FileUpload.State.UPLOADING) {
      jProgress.find('.file-upload-status').text('Uploading');
      let percent = Math.round((sent / total) * 100);
      jProgress.find('.progress-bar').css('width', percent + '%')
      jProgress.find('.progress-bar').text(percent + '%');
    }
    if (state === FileUpload.State.UPLOADED) {
      jProgress.find('.file-upload-status').text('Uploaded');
      let percent = 100;
      jProgress.find('.progress-bar').css('width', percent + '%')
      jProgress.find('.progress-bar').text(percent + '%');
    }
  }

  $('#upload_btn').on('click', (event) => {
    $('#artifact-upload-form .disableable').prop('disabled', true);
    $('#upload_btn').prop('disabled', true);
    $.ajaxSetup({
      async: false
    });
    event.preventDefault();
    event.stopPropagation();
    const uploader = new FileUpload(
      upload_success, upload_progress, upload_error,
      '/upload',
      csrf_token,
    );
    uploader.upload($('#id_file')[0].files[0]);
  });
}


export default {
  props: {
    dataCaseId: String,
    dataCsrfToken: String,
  },
  mounted() {
    register_legacy_uploader(this.dataCaseId, this.dataCsrfToken);
  }
};
</script>
<template>
  <slot/>
</template>
<style lang="scss" scoped>
</style>
