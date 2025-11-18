<template>
  <div class="template-feed-editor">
    <div v-if="this.loading">
      loading data...
    </div>
    <div v-else class="row mt-2">
      <div class="col-6">
        <div class="card">
          <div class="card-body">
            <div class="d-flex justify-content-between border-bottom p-1">
              <div class="h5">
                Template source code
                <span v-if="this.dataReadOnly" class="text-danger">read-only</span>
              </div>
              <Dialog v-model:visible="showDialog" modal header="Available templates">
                <ul>
                  <li v-for="(template, idx) in templates" :key="idx" style="min-width: 15vw; max-width: 65vw">
                    <span class="font-monospace text-primary">{{ template.name }}</span>
                    <Button
                      size="small"
                      severity="primary"
                      variant="text"
                      rounded
                      @click='this.copyToClipboard(`{% include "${template.name}" %}`)'
                      icon="pi pi-copy"
                      aria-label="Copy"/>
                    <span class="text-muted">{{ template.description }}</span>
                  </li>
                </ul>
              </Dialog>
              <div>
                <InputGroup>
                  <Button size="small" severity="secondary" @click="showDialog = true">Available templates</Button>
                  <Button size="small" @click="this.saveAndRender($event)">Render</Button>
                </InputGroup>
              </div>
            </div>
            <div class="mt-2 editor ">
              <CodeMirror
                v-model="this.editedTemplate.content"
                wrap
                basic
                dark
                :extensions="extensions"
                :disabled="this.dataReadOnly"/>
            </div>
          </div>
        </div>
      </div>
      <div class="col-6">
        <div class="card">
          <div class="card-body">
            <div class="d-flex justify-content-between border-bottom p-1">
              <div v-if="this.editedTemplate.in_error" class="h5 text-danger">Output</div>
              <div v-else class="h5">Output</div>
              <Button size="small" @click="this.copyToClipboard(this.renderedContent)">Copy</Button>
            </div>
            <div class="mt-2 editor ">
              <CodeMirror
                v-model="this.renderedContent"
                wrap
                basic
                disabled
                dark
                :extensions="extensions"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import InputText from "primevue/inputtext";
import Textarea from "primevue/textarea";
import Button from 'primevue/button';
import InputGroup from 'primevue/inputgroup';
import Dialog from "primevue/dialog";
import CodeMirror from 'vue-codemirror6';
import {materialDark} from '@ddietr/codemirror-themes/material-dark'

export default {
  props: {
    dataReadOnly: Boolean,
    dataUserId: String,
    dataCaseId: String,
    dataTemplateId: String,
    dataCsrfToken: String,
  },
  components: {
    InputText,
    Textarea,
    Dialog,
    InputGroup,
    Button,
    CodeMirror,
  },
  data() {
    return {
      loading: true,
      internalFeed: null,
      showDialog: false,
      visibilities: null,
      renderedContent: null,
      userDataSource: `/rest/user/${this.dataUserId}`,
      caseDataSource: `/rest/cases/${this.dataCaseId}/internal`,
      editedTemplateDataSource: `/rest/template/${this.dataTemplateId}`,
      visibilitiesDataSource: `/rest/template/visibilities`,
      templatesDataSource: `/rest/template`,
      templates: [],
      editedTemplate: {
        content: "",
        in_error: false,
      },
      extensions: [materialDark],
    }
  },
  created() {
    this.getTemplates();
    this.getEditedTemplate();
    this.loading = false;
  },
  methods: {
    saveAndRender(event) {
      this.renderedContent = "Rendering...";
      this.loading = true;
      if (!this.dataReadOnly) {
        this.save();
      }
      this.render();
      this.loading = false;
    },
    save() {
      $.ajax({
        type: 'PUT',
        async: false,
        url: `${this.editedTemplateDataSource}/`,
        dataType: 'json',
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(this.editedTemplate),
        headers: {
          'X-CSRFToken': this.dataCsrfToken,
        },
        success: (response) => {
          this.$toast.add({severity: "success", summary: "Success", detail: response.message, life: 3000});
        },
        error: (response) => {
          this.$toast.add({severity: "error", summary: "Error", detail: response.message, life: 3000});
        }
      });
    },
    render() {
      $.ajax({
        type: 'GET',
        async: false,
        url: `${this.editedTemplateDataSource}/render?case_id=${this.dataCaseId}`,
        headers: {
          'X-CSRFToken': this.dataCsrfToken,
        },
        success: (response) => {
          this.editedTemplate.in_error = false;
          this.renderedContent = response;
        },
        error: (response) => {
          this.editedTemplate.in_error = true;
          this.renderedContent = response.responseText;
        }
      });
    },
    copyToClipboard(content) {
      navigator.clipboard.writeText(content);
    },
    async getEditedTemplate() {
      try {
        const response = await fetch(this.editedTemplateDataSource);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
        this.editedTemplate = await response.json();
        if (!this.success) {
          throw new Error("Unable to load data");
        }
      } catch (error) {
        this.$toast.add({severity: "error", summary: "Failed", detail: error.message, life: 3000});
      }
    },
    async getTemplates() {
      try {
        const response = await fetch(this.templatesDataSource);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
        this.templates = await response.json();
        if (!this.success) {
          throw new Error("Unable to load data");
        }
      } catch (error) {
        this.$toast.add({severity: "error", summary: "Failed", detail: error.message, life: 3000});
      }
    },
    async getCaseData() {
      try {
        const response = await fetch(this.caseDataSource);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
        this.internalFeed = await response.json();
        if (!this.success) {
          throw new Error("Unable to load data");
        }
        this.$themeUtils.attachStyleToEntities(this.entities).then(() => {
        });
      } catch (error) {
        this.$toast.add({severity: "error", summary: "Failed", detail: error.message, life: 3000});
      }
    },
  },
}
</script>

<style scoped>
.editor {
  height: 80vh;
  overflow: auto;
}
</style>
