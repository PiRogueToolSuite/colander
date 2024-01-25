import {vueComponent} from '../vues_components/vue-sub-component';

jQuery(function ($) {
    //  Search toolbar
    let tbs = vueComponent('colander-toolbar-search');
    $('#toolbar-search').empty().append(tbs);
    //  Key-value pair table
    if ($('textarea#id_attributes').length > 0) {
        let hst = vueComponent('colander-hstore-table-edit');
        $('textarea#id_attributes').after(hst);
    }
});
