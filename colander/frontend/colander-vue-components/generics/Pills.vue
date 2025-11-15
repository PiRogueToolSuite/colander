<template>
  <span class="entity-pills">
    <i v-if="this.entity.superTypeStyle.color" class="fa fa-circle" :style="{ color: this.entity.superTypeStyle.color}"></i>
    <i v-else class="fa fa-circle" style="color: #aaaaaa"></i>

    <i v-if="this.entity.tlp === 'WHITE'" class="fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:CLEAR"></i>
    <i v-if="this.entity.tlp === 'CLEAR'" class="fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:CLEAR"></i>
    <i v-if="this.entity.tlp === 'GREEN'" class="fa fa-circle text-success" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:GREEN"></i>
    <i v-if="this.entity.tlp === 'AMBER'" class="fa fa-circle text-warning" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:AMBER"></i>
    <i v-if="this.entity.tlp === 'RED'" class="fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="TLP:RED"></i>

    <i v-if="this.entity.pap === 'WHITE'" class="fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:CLEAR"></i>
    <i v-if="this.entity.pap === 'CLEAR'" class="fa fa-circle text-muted" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:CLEAR"></i>
    <i v-if="this.entity.pap === 'GREEN'" class="fa fa-circle text-success" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:GREEN"></i>
    <i v-if="this.entity.pap === 'AMBER'" class="fa fa-circle text-warning" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:AMBER"></i>
    <i v-if="this.entity.pap === 'RED'" class="fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="PAP:RED"></i>

    <i v-if="this.entity.associated_threat" class="fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="Malicious"></i>
    <i v-else-if="this.entity.super_type.short_name === 'THREAT'" class="fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="Malicious"></i>
    <i v-else-if="this.entity.attributes && this.entity.attributes.is_malicious" class="fa fa-circle text-danger" data-bs-toggle="tooltip" data-bs-placement="top" title="Malicious"></i>
    <i v-else class="fa fa-circle text-muted"></i>

  </span>
</template>

<script>
export default ({
  props: {
    entity: Object,
  }
})
</script>

<style scoped>
  .fa {
    margin-right: 3px;
  }
</style>
