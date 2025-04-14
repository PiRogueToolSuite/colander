<script>

import Masonry from 'masonry-layout';

function legacy_wait($vue) {
  setTimeout(function () {
    $vue.$debug('#id_force_update', $('#id_force_update'));
    $vue.$debug('#investigate_form',$('#investigate_form'));
    $('#id_force_update').prop('checked', false);
    $('#investigate_form').submit();
  }, 5000);
}

// Mermaid graph of the results from Threatr
async function legacy_init($vue) {

  $('#tabs-menu button[role=tab]').on('shown.bs.tab', function () {
    let target = $(this).attr('data-bs-target');
    $vue.$debug('tab shown', this, 'target', target);
    let masonryElem = $(target).find('.masonry-row');
    if (masonryElem.length > 0) {
      $vue.$debug('masonry content found');
      masonryElem.each(function() {
        $vue.$debug('Masonry element', this);
        if ($(this).data('masonry')) {
          $vue.$debug('Masonry element already initialized', this);
          $(this).data('masonry').layout();
        }
        else {
          let masonry = new Masonry(this, {itemSelector: '.masonry-card', percentPosition: true});
          $(this).data('masonry', masonry);
          $vue.$debug('Masonry element initialized', masonry);
        }
      });
    }
    else {
      $vue.$debug('no masonry content for this tab');
    }
  });

  // Listen on the "Add to current case buttons" to import a result into the current case.
  $('.investigate-add-entity-btn').click(async function (e) {
    console.log('.investigate-add-entity-btn', 'click', this);
    const data = JSON.parse($('#results-data').text());
    const id = $(this).attr('data-obj-id');
    const root = data['root_entity'];
    let relation = undefined;
    let entity = undefined;
    let event = undefined;
    data['events'].forEach(function (e) {
      if (e.id === id) {
        event = e;
        event.super_type = {name: 'Event', short_name: 'EVENT'};
      }
    });
    if (id !== root['id']) {
      entity = data['entities'][id];
      if (entity !== undefined) {
        data['relations'].forEach(function (r) {
          if ((r.obj_from == root.id && r.obj_to == entity.id) || (r.obj_to == root.id && r.obj_from == entity.id)) {
            relation = r;
          }
        });
      }
    }

    const response = await fetch(`/rest/threatr_entity`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': $vue.dataCsrfToken,
      },
      body: JSON.stringify({
        'case_id': $vue.dataCaseId,
        'root': root,
        'entity': entity,
        'event': event,
        'relation': relation
      })
    });

    const json_response = await response.json()
    $(this).removeClass('bg-primary');
    $(this).unbind('click');
    if (json_response.status === 0) {
      $(this).addClass('bg-success');
    } else {
      $(this).addClass('bg-danger');
    }
  });
}

export default {
  props: {
    'class': String,
    'dataWait': Boolean,
    'dataCsrfToken': String,
    'dataCaseId': String,
  },
  data() {
    return {};
  },
  created() {
    this.$logger(this, 'InvestigateView');
  },
  mounted() {
    if (this.dataWait) {
      legacy_wait(this);
    }
    legacy_init(this);
    this.$info('mounted');
  },
  methods: {

  },
  computed: {

  },
};
</script>
<template>
</template>
