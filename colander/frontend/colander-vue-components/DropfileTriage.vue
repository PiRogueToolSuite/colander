<script>
function legacy_bind($vue) {
  let suggestedArtifactTypesInformation = $("<span class='ms-1 text-secondary'></span>");
  $('#hint_id_type').append(suggestedArtifactTypesInformation);

  fetch('/rest/artifact_types/').then(async (response) => {
    let ats_array = await response.json();
    for(let at of ats_array) {
      Colander.Cache.store('artifact_type', at.id, at);
    }
  }).catch((e) => {
    console.error('', e);
  });

  async function drops_review() {
    // 1. Get all selected drops
    let df_ids = $('#div_id_dropped_files input[name=dropped_files]:checked').map((idx, el) => {
      return $(el).val();
    }).get();
    for (let dfId of df_ids) {
      if (!Colander.Cache.contains('dropped_file', dfId)) {
        let dropResponse = await fetch(`/rest/drops/${dfId}/`);
        if (!dropResponse.ok) {
          console.error("Can not retrieve DroppedFile information");
          throw new Error("Can not retrieve DroppedFile information");
        }
        let drop = await dropResponse.json();
        let suggested_artifact_types = await suggest_artifact_type(drop);
        drop.suggested_artifact_types = suggested_artifact_types;
        Colander.Cache.store('dropped_file', drop.id, drop);
      }
    }

    // 2. Set UI stuff against selected drops
    $('#triage-modal').toggleClass('batch', df_ids.length > 1);

    // 2.1. batch or not, fills case and suggestions
    // 2.1.1. merge all suggested artifact types
    let all_suggested_types = {};
    for (let dfId of df_ids) {
      let d = Colander.Cache.get('dropped_file', dfId);
      for (let sat of d.suggested_artifact_types) {
        all_suggested_types[sat.id] = all_suggested_types[sat.id] || {count: 0};
        all_suggested_types[sat.id] = Object.assign(
          all_suggested_types[sat.id],
          sat
        );
        all_suggested_types[sat.id].count++;
      }
    }

    // 2.1.2. Set suggestion string helper in UI
    let ast_str = $.map(all_suggested_types, (e) => e.name).join(', ');
    suggestedArtifactTypesInformation.text(ast_str ? `Suggested: ${ast_str}` : '');

    // 2.1.3. Peak one and set it in UI
    let suggested_artifact_type_id = '';
    if (Object.keys(all_suggested_types).length > 0) {
      suggested_artifact_type_id = Object.keys(all_suggested_types)[0]
    }
    $('#id_type').val(suggested_artifact_type_id).change();

    // 2.2. Depending on batch state
    if (df_ids.length > 1) {
      // With multiple dropped_file triage
      // we will let server fills name/source_url
      $('#id_name').val('');
      $('#id_source_url').val('');
    } else {
      let drop = Colander.Cache.get('dropped_file', df_ids[0]);
      $('#id_name').val(drop.filename);
      $('#id_source_url').attr('readonly', Boolean(drop.attributes['source_url']));
      $('#id_source_url').val(drop.attributes['source_url'] || '');
    }

    // 3. Case suggestion
    let all_suggested_cases = {};
    for (let dfId of df_ids) {
      let d = Colander.Cache.get('dropped_file', dfId);
      if (!d.case) continue;
      all_suggested_cases[d.case] = all_suggested_cases[d.case] || { count: 0 };
      all_suggested_cases[d.case].count++;
    }
    let suggested_case_id = '';
    if (Object.keys(all_suggested_cases).length > 0) {
      suggested_case_id = Object.keys(all_suggested_cases)[0]
    }
    $('#id_case').val(suggested_case_id).change();

    // 4. Show to user
    $('#triage-case-tab').tab('show');
    $('#triage-modal').modal('show');
  }

  async function suggest_artifact_type(droppedFile) {
    let suggestResponse = null;

    let suggest_method = 'suggest_by_mimetype';
    let suggest_method_body_request = { mime_type: droppedFile.mime_type };

    if (!droppedFile.mime_type) {
      suggest_method = 'suggest_by_filename';
      suggest_method_body_request = {
        'filename': droppedFile.filename,
      };
    }

    suggestResponse = await fetch(`/rest/artifact_types/${suggest_method}/`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': $vue.dataCsrfToken,
      },
      body: JSON.stringify(suggest_method_body_request),
    });

    // Fail safe, since suggesting are QOL
    if (!suggestResponse.ok) return [];

    let artifactTypes = await suggestResponse.json();

    return artifactTypes;
  }

  async function case_change() {
    $('#triage-case button[role=next]').attr('disabled', true);
    let caseId = $('#id_case').val();
    if (!caseId) return;

    let caseObj = null;
    if (Colander.Cache.contains('case', caseId)) {
      caseObj = Colander.Cache.get('case', caseId);
    }
    else {
      let caseResponse = await fetch(`/rest/cases/${caseId}/`);
      if (!caseResponse.ok) {
        throw new Error("Can not retrieve Case information");
      }
      caseObj = await caseResponse.json();

      // Populate case devices
      let devicesResponse = await fetch(`/rest/cases/${caseId}/devices/`)
      caseObj.devices = await devicesResponse.json();

      Colander.Cache.store('case', caseId, caseObj);
    }

    // Set values depending on Case
    $('#id_tlp').val(caseObj.tlp);
    $('#id_pap').val(caseObj.pap);
    // Generate device <select>
    let jOptions = [];
    jOptions.push($(`<option value=''>---------</option>`));
    for( let devId in caseObj.devices ) {
      jOptions.push($(`<option value='${devId}'>${caseObj.devices[devId].name}</option>`));
    }
    $('#id_extracted_from').empty().append(jOptions);

    $('#triage-case button[role=next]').attr('disabled', false);
  }

  async function artifact_type_change() {
    $('#triage-artifact button[role=next]').attr('disabled', true);

    let artifact_type = $('#id_type').val();
    if (!artifact_type) return;

    $vue.notifyEntityTypeChanged(artifact_type);

    let selected_at = Colander.Cache.get('artifact_type', artifact_type);
    if (selected_at.default_attributes) {
      $('#id_attributes').val(JSON.stringify(selected_at.default_attributes));
      let editorVue = $('#colander-hstore-table-edit-1').data('vue');
      //editorVue.dataLoaded = false;
      //editorVue.attributes;
    }

    $('#triage-artifact button[role=next]').attr('disabled', false);
  }

  async function update_dropped_files_selection() {
    let df_check_id = $(this).val();
    let df_checked = $(this).prop('checked');

    $(`input[name=dropped_files][value=${df_check_id}]`).prop(
      'checked', df_checked);

    let selected_dropped_files_count = $('input[name=dropped_files]:checked').length;
    $('#triage-actions button').attr('disabled', selected_dropped_files_count<1);
    $('#triage-actions .badge')
      .text(`${selected_dropped_files_count}`)
      .toggle(selected_dropped_files_count>1);
  }

  $('.dropped-file-selection-checkbox')
    .change(update_dropped_files_selection)
    .trigger('change'); // Force updating state if 'reloading' page

  $('#triage-case button[role=next]').click(() => {
    $('#triage-artifact-tab').tab('show');
  });

  $('#triage-artifact button[role=previous]').click(() => {
    $('#triage-case-tab').tab('show');
  });
  $('#triage-artifact button[role=next]').click(() => {
    $('#triage-attributes-tab').tab('show');
  });

  $('#triage-attributes button[role=previous]').click(() => {
    $('#triage-artifact-tab').tab('show');
  });
  $('#triage-attributes button[role=next]').click(() => {
    $('#triage-details-tab').tab('show');
  });

  $('#triage-details button[role=previous]').click(() => {
    $('#triage-attributes-tab').tab('show');
  });

  $('#triage-details button[role=convert]').click(() => {
    $('#triage-form').submit();
  });

  $('#triage-actions button[role=delete]').on('click',() => {
    $('#id_delete_action').val('delete');
    $('#triage-form').submit();
  });

  $('#id_type').change(artifact_type_change);
  $('#id_case').change(case_change);
  $('#triage-actions button[role=review]').click(drops_review);
}
export default {
  props: {
    dataCsrfToken: String,
  },
  mounted() {
    this.$logger(this, 'DropfileTriage');
    this.$debug('mounted');
    legacy_bind( this );
  },
  methods: {
    notifyEntityTypeChanged(entityType) {
      this.$debug('notifyEntityTypeChanged', entityType);
      this.$bus.emit('entity-type-changed', entityType);
    },
  }
}
</script>
<template>
  <slot name="listing" />
  <Teleport to="body">
    <slot name="modal" />
  </Teleport>
</template>
<style lang="scss">
  #triage-modal .batch-elem {
    display: none;
  }
  #triage-modal.batch {
    .batch-elem {
      display: initial;
    }
    .non-batch-elem {
      display: none;
    }
  }
  #triage-form .tab-pane .modal-body
  {
  }
</style>
