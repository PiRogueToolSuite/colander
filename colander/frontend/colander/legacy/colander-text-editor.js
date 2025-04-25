async function resolve_codemirror() {
  const codemirror_concerns = $('textarea.colander-text-editor, pre.colander-text-editor > code');
  if (codemirror_concerns.length > 0) {
    const {
      ayuLight,
      basicSetup,
      EditorState,
      EditorView
    } = await import(/* webpackChunkName: "ascodemirror" */ './async-codemirror');

    function editorFromTextArea(textarea, extensions) {
      let view = new EditorView({
        doc: textarea.value,
        extensions
      });
      $(view.dom).height('52em');
      $(view.dom).css({
        'overflow': 'auto',
        'max-width': '100%',
        'border': '1px solid #c4c3c8',
        'border-radius': '8px'
      });
      textarea.parentNode.insertBefore(view.dom, textarea);
      $($(textarea.form), $('button[type=submit]')).click(() => {
        textarea.value = view.state.doc.toString();
      });
      if (textarea.form) textarea.form.addEventListener("submit", () => {
        textarea.value = view.state.doc.toString();
      });
      return view;
    }

    // Replace textarea with a text editor
    $('textarea.colander-text-editor').each(function (index, elt) {
      const extensions = [
        EditorView.contentAttributes.of({contenteditable: true}),
        basicSetup,
        ayuLight,
      ];
      editorFromTextArea(elt, extensions);
      $(this).css('visibility', 'hidden');
      $(this).css('position', 'absolute');
    });

    // Replace pre > code with a text editor in read-only mode
    $('pre.colander-text-editor > code').each(function (index, elt) {
      let view = new EditorView({
        doc: elt.innerHTML,
        state: EditorState.create({
          doc: elt.innerHTML,
          extensions: [
            EditorView.contentAttributes.of({contenteditable: false}),
            ayuLight,
            basicSetup,
            EditorView.lineWrapping,
          ],
        }),
      });
      $(view.dom).css({
        'max-height': '64em',
        'overflow': 'auto',
        'border': '1px solid #c4c3c8',
        'border-radius': '8px'
      });

      elt.parentNode.parentNode.insertBefore(view.dom, elt.parentNode);
      $(this).removeClass();
      $(this).parent().remove();
    });
  }
}

export default () => {
  resolve_codemirror().catch(console.error);
};
