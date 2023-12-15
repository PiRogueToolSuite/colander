import {vueComponent} from '../vues_components/vue-sub-component';

jQuery(function($) {
   let tbs = vueComponent('colander-toolbar-search');
   $('#toolbar-search').empty().append(tbs);
});
