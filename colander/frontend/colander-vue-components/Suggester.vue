<script>
export default {
  props: {
    dataCsrfToken: String,
    dataCaseId: String,
    dataType: String,
  },
  data() {
    return {
      loading: false,
      result: { data: [] },
    };
  },
  mounted() {
    this.$input = this.$refs.slotContent.querySelector('input[name=name]');
    this.$input.addEventListener('input', this.suggest.bind(this));
    $(this.$input).attr('autocomplete', 'off');
  },
  methods: {
    suggest() {
      const value = $(this.$input).val().trim();
      if (value.length > 4) {
        this.loading = true;
        $.ajax({
          type: 'POST',
          url: '/rest/entity/suggest',
          dataType: 'json',
          data: {
            type: this.dataType,
            value: value,
            case_id: this.dataCaseId || null,
          },
          headers: {
            'X-CSRFToken': this.dataCsrfToken,
          },
          success: (data) => {
            this.result.data = data;
            this.loading = false;
            $(this.$refs.tooltip).tooltip('show');
          },
          error: () => {
            this.loading = false;
          }
        });
      }
      else {
        this.result.data = [];
      }
    },
  },
};
</script>

<template>
  <div ref="slotContent" class="suggester">
    <slot/>
    <div class="text-muted mb-0 suggested-entity" v-for="d in result.data">
      Do you mean <a :href="d.url" class="">{{d.text}}</a> ?
    </div>
  </div>
</template>

<style lang="scss" scoped>
.suggester
{
  position: relative;

  .suggester-hint
  {
    position: absolute;
    left: -1.25rem;
    height: 2rem;
    width: 2rem;
  }
  .suggested-entity
  {
    display: none;
    position: absolute;
    background-color: rgba(var(--bs-body-bg-rgb), 0.9);
    border: solid var(--bs-border-color) var(--bs-border-width);
    border-radius: var(--bs-border-radius-sm);
    text-align: left;
    width: 100%;
    top: 4rem;
    z-index: 10000;
    padding: 0.1rem 1em;
    box-sizing: border-box;
    backdrop-filter: blur(1px);
  }

  &:focus-within
  {
    .suggested-entity {
      display: block;
    }
  }
}
</style>
