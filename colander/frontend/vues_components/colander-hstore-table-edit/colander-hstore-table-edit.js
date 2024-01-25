new Vue({
    delimiters: ['[[', ']]'],
    data: {
        textArea: $('textarea#id_attributes'),
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
            this.$set(this.storedAttributes, this.storedAttributes.length, {key: 'new_key', value: 'value'});
        },
        update_json: function(){
            let obj = {};
            for (let i in this.storedAttributes){
                obj[this.storedAttributes[i].key] = this.storedAttributes[i].value;
            }
            try {
                this.textArea.val(JSON.stringify(obj));
            } catch (TypeError){}
        }
    },
    computed: {
        attributes: function () {
            if (!this.dataLoaded) {
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
    }
});
