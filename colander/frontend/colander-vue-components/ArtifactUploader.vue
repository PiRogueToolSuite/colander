<script>

import FileUpload from './legacy/file_upload';

function register_legacy_uploader(case_id) {

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
    $('#upload_submit_btn').visible();

    $('#artifact-upload-form').submit();
  }

  function upload_error(data) {
    $('#id_file').prop('disabled', false);
    $('#artifact-upload-form .disableable').prop('disabled', false);
    $('#upload_btn').prop('disabled', false);
    console.error('upload_error', data);
    if (typeof data === 'string') {
      alert(data);
    }
    else {
      alert('Unable to upload your file. Please refresh this page and contact your administrator.');
    }
  }

  function upload_progress(data, sent, total) {
    console.log('upload_progress', arguments);
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
      $('#id_file')[0],
      //$('#artifact-upload-file')[0],
      upload_success, upload_progress, upload_error,
      `/ws/${ case_id }/collect/artifact/upload`,
    );
    uploader.upload();
  });
}


export default {
  props: {
    dataCaseId: String,
  },
  mounted() {
    register_legacy_uploader(this.dataCaseId);
  }
};
</script>
<template>
  <slot/>
</template>
<style lang="scss" scoped>
</style>
