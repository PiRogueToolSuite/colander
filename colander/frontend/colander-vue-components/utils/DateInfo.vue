<script>
import { intlFormat, intlFormatDistance } from 'date-fns';

function _floorish(val) {
  return Math.sign(val) * Math.floor(Math.abs(val));
}

export default {
  props: {
    date:String,
  },
  created() {
    console.log('intlFormat', intlFormat('2024-08-01T13:18:43.475527Z', { locale: 'fr-FR' }));
    this.nowRef = new Date();
  },
  computed: {
    dateObj() {
      console.log('date', this.date)
      return new Date(this.date);
    },
    localizedDate() {
      console.log('dateObj', this.dateObj);
      //return intlFormat(this.date, { locale: 'fr-FR' });
      const options = {
        year: "numeric",
        month: "short",
        day: "numeric",
        //hour: "long",
        //dateStyle: 'medium',
        //timeStyle: "medium",
      };
      return this.dateObj.toLocaleDateString(undefined, options);
    },
    localizedTime() {
      console.log('dateObj', this.dateObj);

      //return intlFormat(this.date, { locale: 'fr-FR' });
      const options = {
        timeStyle: 'short',
      };
      return this.dateObj.toLocaleTimeString(undefined, options);
    },
    timesince() {
      //return intlFormatDistance(this.date, { locale: 'fr-FR' });
      //return 'since' + String(this.dateObj);
      let diffMillis = this.dateObj.getTime() - this.nowRef.getTime();
      let diffSeconds = diffMillis / 1000;
      let diffMinutes = diffSeconds / 60;
      let diffHours = diffMinutes / 60;
      let diffDays = diffHours / 24;
      let diffMonthMean = diffDays / 30.4375; // == Year and quarter / 12
      let diffYearsMean = diffMonthMean / 12;
      if (Math.abs(diffYearsMean) > 1)
        return new Intl.RelativeTimeFormat().format(_floorish(diffYearsMean), 'year');
      if (Math.abs(diffMonthMean) > 1)
        return new Intl.RelativeTimeFormat().format(_floorish(diffMonthMean), 'month');
      if (Math.abs(diffDays) > 1)
        return new Intl.RelativeTimeFormat().format(_floorish(diffDays), 'day');
      if (Math.abs(diffHours) > 1)
        return new Intl.RelativeTimeFormat().format(_floorish(diffHours), 'hour');
      return new Intl.RelativeTimeFormat().format(_floorish(diffMinutes), 'minute');
    },
  }
};
</script>
<template>
  <span v-if="date">
    <i class="nf nf-fa-calendar"></i>
    <span class="ms-1">{{ localizedDate }} {{ localizedTime }}</span>
    <span class="text-muted ms-1">
      <i class="fa fa-clock-o"></i>
      <span class="ms-1">{{timesince}}</span>
    </span>
  </span>
</template>
