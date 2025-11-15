<template>
  <div class="misp-importer">
    <div class="row justify-content-center">
      <div class="col-md-12 mt-2">
        <GenericFeedImporter :dataCaseId="this.dataCaseId" :dataCsrfToken="this.dataCsrfToken" feedType="misp">

        </GenericFeedImporter>
      </div>
    </div>
  </div>
</template>

<script>
import GenericFeedImporter from "../generics/GenericFeedImporter.vue";

export default {
  props: {
    dataCaseId: String,
    dataCsrfToken: String,
  },
  components: {
    GenericFeedImporter,
  }
}
</script>

<style scoped>
</style>
