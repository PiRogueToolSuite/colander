new Vue({
    delimiters: ['[[', ']]'],
    data: {
        textArea: $('textarea#id_attributes'),
        entityTypesContainer: $('script#entity_types'),
        storedAttributes: [],
        dataLoaded: false,
    },
    methods: {
        update_key: function (index, event) {
            const newKey = event.target.value;
            if (newKey.length > 0) {
                this.$set(this.storedAttributes, index, {key: newKey, value: this.storedAttributes[index].value});
            }
            this.update_json();
        },
        update_value: function (index, event) {
            const newValue = event.target.value;
            if (newValue.length > 0) {
                this.$set(this.storedAttributes, index, {key: this.storedAttributes[index].key, value: newValue});
            }
            this.update_json();
        },
        delete_attribute: function(index, event){
            this.$delete(this.storedAttributes, index);
            this.update_json();
        },
        add_attribute: function(){
            this.$set(this.storedAttributes, this.storedAttributes.length, {key: 'new_key', value: ''});
        },
        on_type_selection_changed: function (e) {
            const default_attributes = this.entity_types[e.target.value].attributes;
            this.dataLoaded = false; // Reload from textarea
            this.attributes;
            for (let k in default_attributes) {
                if (!this._is_key_stored(k)) {
                    this.$set(this.storedAttributes, this.storedAttributes.length, {key: k, value: default_attributes[k]});
                }
            }
        },
        _is_key_stored: function (k) {
            for (let i in this.storedAttributes) {
                if (this.storedAttributes[i].key === k) {
                    return true
                }
            }
            return false;
        },
        update_json: function(){
            let obj = {};
            for (let i in this.storedAttributes){
                if (this.storedAttributes[i].value)
                    obj[this.storedAttributes[i].key] = this.storedAttributes[i].value;
            }
            try {
                this.textArea.val(JSON.stringify(obj));
            } catch (TypeError){}
        }
    },
    computed: {
        entity_types: function() {
            const types_from_container = this.entityTypesContainer.text();
            if (types_from_container.length > 1) {
                try {
                    return JSON.parse(types_from_container);
                } catch (SyntaxError) {
                }
            }
            return {};
        },
        attributes: function() {
            if (!this.dataLoaded) {
                this.storedAttributes = [];
                let attr_from_textarea = this.textArea.val();
                if (attr_from_textarea.length > 1) {
                    try {
                        const attrs = JSON.parse(attr_from_textarea);
                        let i = 0;
                        for (let k in attrs) {
                            this.$set(this.storedAttributes, i++, {key: k, value: attrs[k]});
                        }
                    } catch (SyntaxError) {}
                }
                this.dataLoaded = true;
            }
            return this.storedAttributes;
        }
    },
    mounted: function(){
        $('textarea#id_attributes').css('visibility', 'hidden');
        $('textarea#id_attributes').css('position', 'absolute');
        $('input[type=radio][name="type"]').on('click', this.on_type_selection_changed);
    }
});
