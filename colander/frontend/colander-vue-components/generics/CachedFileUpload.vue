<template>
  <div class="cached-file-upload">
    <Toast/>
    <div class="row justify-content-center mb-4">
      <div class="col-12">
        <Card>
          <template #content>
            <form method="POST" enctype="multipart/form-data" id="uploadContentForm">
              <input v-if="this.converter" type="hidden" name="converter" id="converter" :value="this.converter">
              <div class="mb-3">
                <label for="fileInput" class="form-label">Select a file</label>
                <input class="form-control" type="file" id="fileInput" name="file">
              </div>
              <div class="mb-3">
                <label for="contentField" class="form-label">or paste content</label>
                <Textarea v-model="this.content" rows="5" cols="30" class="form-control" id="contentField" name="content" />
              </div>
              <Button
                label="Load"
                severity="primary"
                icon="pi pi-cloud-upload"
                @click="this.uploadContent"
              />
            </form>
          </template>
        </Card>
      </div>
    </div>
    <div v-if="$slots.next && this.success" class="row justify-content-center">
      <div class="col-12">
        <slot v-if="this.success" name="next" :cachedFile="this.cachedFile" :dataSource="this.dataSource"></slot>
      </div>
    </div>
  </div>
</template>

<script>
import Toast from "primevue/toast";
import Button from "primevue/button";
import Card from 'primevue/card';
import Textarea from 'primevue/textarea';

export default {
  components: {
    Toast,
    Card,
    Button,
    Textarea,
  },
  data() {
    return {
      content: "",
      cachedFile: "",
      success: false,
    };
  },
  props: {
    dataCaseId: String,
    dataCsrfToken: String,
    converter: String,
  },
  computed: {
    dataSource() {
      return "/rest/cached/" + this.cachedFile;
    }
  },
  methods: {
    uploadContent(event) {
      const formData = new FormData($('#uploadContentForm')[0]);
      $.ajax({
        type: "POST",
        url: "/rest/cached",
        dataType: 'json',
        processData: false,
        contentType: false,
        data: formData,
        headers: {
          "X-CSRFToken": this.dataCsrfToken,
        },
        success: (response) => {
          this.cachedFile = response.uuid;
          this.success = true;
          this.content = "";
          this.$toast.add({severity: "success", summary: "Success", detail: "Content uploaded", life: 3000});
        },
        error: (response) => {
          this.$toast.add({severity: "error", summary: "Failed", detail: response.responseJSON.message, life: 3000});
        }
      });
    }
  }
};
</script>

<style scoped>
.p-card {
  background: #ececec;
}
</style>
