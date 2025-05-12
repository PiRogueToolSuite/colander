<template>
  <div ref="map-root" class="w-100" style="height: 200px">
  </div>
</template>

<script>
  import {Feature, Map, View} from 'ol/index';
  import {OSM, Vector as VectorSource} from 'ol/source';
  import {Point} from 'ol/geom';
  import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer';
  import {useGeographic} from 'ol/proj';
  import 'ol/ol.css'

  export default {
    name: 'GeoMap',
    components: {},
    props: {
      dataLatitude: String,
      dataLongitude: String
    },
    mounted() {
      useGeographic();
      const place = [Number(this.dataLongitude), Number(this.dataLatitude)];
      const point = new Point(place);
      new Map({
        target: this.$refs['map-root'],
        layers: [
          new TileLayer({
            source: new OSM(
              {
              }
            )
          }),
          new VectorLayer({
          source: new VectorSource({
            features: [new Feature(point)],
          }),
          style: {
            'circle-radius': 8,
            'circle-fill-color': '#7122da',
            'circle-stroke-width': 4,
            'circle-stroke-color': "#a991d4",
          },
        }),
        ],
        view: new View({
          zoom: 6,
          center: place,
          constrainResolution: true
        }),
      })

    },
  }
</script>
