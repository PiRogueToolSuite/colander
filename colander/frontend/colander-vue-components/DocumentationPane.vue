<script setup>
//import SimpleMde from 'simplemde';
//FIXME: Import not supported for simplemde: This library is not package to support 'import'
//TODO: Change to another Markdown visual editor library
</script>
<script>
export default {
  props: {
    dataCaseId: String,
    dataSrc: String,
    dataOffCanvas: Boolean,
  },
  data() {
    return {
      contextual_case: {},
      textarea_jElem: null,
      autosave_on: false,
      doc_content_server: null,
    };
  },
  mounted() {
    this.textarea_jElem = $(this.$refs.slotContent).find('#id_documentation');
    this.documentation_save_jElem = $(this.$refs.slotContent).find('#id_documentation');
    this.doc_content_server = this.documentationContent;

    // Check autosave state
    try {
      let unsaved_case_doc = localStorage.getItem(this.itemKey);
      if (unsaved_case_doc !== null && unsaved_case_doc !== '') {
        this.textarea_jElem?.val(unsaved_case_doc);
        this.set_dirty(true);
        this.set_revertable(true);
        $(this.$refs.unsavedCaseDocumentationModal).modal('show');
      }
    } catch(err) {
      console.log('Unavailable local storage');
    }

    // Creates markdown editor view
    this.non_reactive_simplemde = new SimpleMDE(
      {
        autoDownloadFontAwesome: false,
        spellChecker: false,
        element: this.textarea_jElem?.[0],
        status: false,
      }
    );

    // Register documentation changes event to:
    // - enable autosave feature
    // - register a 'page exit' event to force autosave
    this.non_reactive_simplemde.codemirror.on("change", () => {
      this.set_dirty(true);
      this.set_revertable(true);
    });

    //
    // UX Events
    $('#case_documentation_form').on('submit', () => {
      this.clear_autosave();
    });

    $('#documentation-save').click(() => {
      $('#case_documentation_form').submit();
    });

    $('#documentation-revert').click(() => {
      this.revert_to_server_version();
    });

    window.addEventListener('beforeunload', (evt) => {
      if (!this.autosave()) {
        // Current device could not use localstorage
        // We need to warn user about losing unsaved documentation.
        evt.preventDefault();
        evt.stopPropagation();
        this.reviewDocumentationNow();
        $(this.$refs.unsavedDocumentationChangesToast).toast('show');
        return false;
      }
    });
  },
  methods: {
    set_dirty(dirty) {
      $('#documentation-save').attr('disabled', !dirty);
      this.autosave_on = dirty;
    },
    set_revertable(revertable) {
      $('#documentation-revert').attr('disabled', !revertable);
    },
    clear_autosave() {
      this.autosave_on = false;
      try {
        localStorage.removeItem(this.itemKey);
      } catch(err) {
        console.log('Unavailable local storage');
      }
    },
    revert_to_server_version() {
      this.non_reactive_simplemde.value(this.doc_content_server);
      this.set_dirty(false);
      this.set_revertable(false);
      this.clear_autosave();
    },
    autosave() {
      if (this.autosave_on) {
        try {
          localStorage.setItem(this.itemKey, this.non_reactive_simplemde.value());
        } catch(err) {
          console.warn('Local storage not available');
          return false;
        }
      }
      return true;
    },
    reviewDocumentationNow() {
      $('#documentationOffCanvas').offcanvas("show");
    },
  },
  computed: {
    documentationContent() {
      return this.textarea_jElem?.val();
    },
    itemKey() {
      return `case-doc-${this.dataCaseId}`;
    }
  },
};
</script>
<template>
  <div ref="slotContent">
    <slot/>
  </div>
  <Teleport to="body">
    <div class="position-fixed bottom-0 end-0 m-3" style="z-index: 5000">
      <div id="unsaved-doc-changes-toast"
           ref="unsavedDocumentationChangesToast"
           class="toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
          <strong class="me-auto text-primary">Unsaved documentation changes</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
          <p>You have unsaved documentation changes on this device.</p>
        </div>
      </div>
    </div>
  </Teleport>
  <Teleport to="body">
    <div id="unsaved-case-documentation-modal"
         ref="unsavedCaseDocumentationModal"
         class="modal fade"  tabindex="-1" role="dialog" aria-labelledby="unsaved-case-documentation-modal-title" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title text-primary" id="unsaved-case-documentation-modal-title"><i class="nf nf-fa-warning text-warning"></i> Unsaved documentation</h5>
          </div>
          <div class="modal-body">
            <p>You have unsaved documentation changes on this device.</p>
            <p>These changes have been saved temporarily on this device but not submitted to the server.</p>
            <p>Note: Changes will be lost if you use revert action.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Remind me later</button>
            <button type="button"
                    @click="reviewDocumentationNow"
                    class="btn btn-primary" data-bs-dismiss="modal" role="review-documentation">Review now</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
<style scoped>
</style>
