<script>
export default {
  props: {
    tlp:String,
    pap:String,
  },
  mounted() {
    $(this.$el).find('[data-bs-toggle=tooltip]').each((idx,el)=>{
      if ($(el).is('[data-level-type=tlp]')) {
        new bootstrap.Tooltip(el, {
          title: () => this.tlpTitle
        });
      }
      if ($(el).is('[data-level-type=pap]')) {
        new bootstrap.Tooltip(el, {
          title: () => this.papTitle
        });
      }
    });
  },
  method: {
    title() {
      return this.tlpTitle;
    }
  },
  computed: {
    tlpTitle() {
      switch(this.tlp) {
        case 'WHITE':
        case 'CLEAR':
          return "Recipients can spread this to the world, there is no limit on disclosure.";
        case 'GREEN':
          return "Limited disclosure, recipients can spread this within their community.";
        case 'AMBER':
          return "Limited disclosure, recipients can only spread this on a need-to-know basis within their organization and its clients.";
        case 'RED':
          return "For the eyes and ears of individual recipients only, no further disclosure.";
      }
    },
    papTitle() {
      switch(this.pap) {
        case 'WHITE':
        case 'CLEAR':
          return "No restrictions in using this information.";
        case 'GREEN':
          return "Active actions allowed. Recipients may use PAP:GREEN information to ping the target, block incoming/outgoing traffic from/to the target or specifically configure honeypots to interact with the target.";
        case 'AMBER':
          return "Passive cross check. Recipients may use PAP:AMBER information for conducting online checks, like using services provided by third parties (e.g. VirusTotal), or set up a monitoring honeypot.";
        case 'RED':
          return "Non-detectable actions only. Recipients may not use PAP:RED information on the network. Only passive actions on logs, that are not detectable from the outside.";
      }
    },
    tlpContent() {
      switch(this.tlp) {
        case 'WHITE':
          return 'CLEAR';
        default:
          return this.tlp;
      }
    },
    papContent() {
      switch(this.pap) {
        case 'WHITE':
          return 'CLEAR';
        default:
          return this.pap;
      }
    },
    tlpClasses() {
      let classes = ['badge', 'bg-dark'];
      switch(this.tlp) {
        case 'WHITE':
        case 'CLEAR':
          classes.push('text-light');
          break;
        case 'GREEN':
          classes.push('text-success');
          break;
        case 'AMBER':
          classes.push('text-warning');
          break;
        case 'RED':
          classes.push('text-danger');
          break;
      }
      return classes;
    },
    papClasses() {
      let classes = ['badge', 'bg-dark'];
      switch(this.pap) {
        case 'WHITE':
        case 'CLEAR':
          classes.push('text-light');
          break;
        case 'GREEN':
          classes.push('text-success');
          break;
        case 'AMBER':
          classes.push('text-warning');
          break;
        case 'RED':
          classes.push('text-danger');
          break;
      }
      return classes;
    },
  },
}
</script>
<template>
  <span>
    <span v-show="tlp"
          :class="tlpClasses" class="me-1"
          data-level-type="tlp"
          data-bs-toggle="tooltip" data-bs-placement="top">
      TLP:{{tlpContent}}
    </span>
    <span v-show="pap"
          :class="papClasses"
          data-level-type="pap"
          data-bs-toggle="tooltip" data-bs-placement="top">
      PAP:{{papContent}}
    </span>
  </span>
</template>
