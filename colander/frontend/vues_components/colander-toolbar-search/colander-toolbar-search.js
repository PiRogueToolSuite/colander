new Vue({
    delimiters: ['[[', ']]'],
    data: {
        currentSearch: '',
        results: [],
    },
    methods: {
        updateResult: async function() {
            const csrfDom = document.querySelector("#overall-search-form input[name=csrfmiddlewaretoken]");
            const caseIdDom = document.querySelector("#overall-search-form input[name=case_id]");
            var queryPost = {
                case_id: caseIdDom?.value,
                query: this.currentSearch,
            };
            try {
                const searchResponse = await fetch('/rest/search', {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfDom.value,
                    },
                    body: JSON.stringify(queryPost),
                });
                if (!searchResponse.ok) {
                  throw new Error('Unexcpeted server error');
                }
                this.results = await searchResponse.json();
            } catch(e) {
                console.error("Unable to search", e);
            }
        },
        startDrag(evt, item) {
            console.log('startDrag', evt, item);
            evt.dataTransfer.dropEffect = "link";
            evt.dataTransfer.setData("text/markdown", `[${item.name}](${item.url})`);
        }
    },
    watch: {
        currentSearch(newValue, oldValue) {
            if (this._debounced_handler) {
                clearTimeout(this._debounced_handler);
                this._debounced_handler = null;
            }
            this._debounced_handler = setTimeout(this.updateResult.bind(this), 300);
        }
    },
    computed: {},
});
//# sourceURL=webpack://colander/./colander/frontend/vues_components/colander-toolbar-search/colander-toolbar-search.js
