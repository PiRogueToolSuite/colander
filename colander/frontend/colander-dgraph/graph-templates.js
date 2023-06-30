
import {icons, color_scheme} from './default-style';
import {date_str} from './utils';

export const overlay_button = (icon, label, title) => {
  title = title || label;
  return $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="${title}">
      <i class="fa ${icon}" aria-hidden="true"></i>
      <span class="label">${label}</span>
    </button>`);
};

function to_edit_url(url) {
    return url.replace(/\/details$/,'');
}

export const details_view = (ctx, styles) => {
  let view = $(`<div class='container'>
      <div class='mt-2 mb-2'><i class='fa fa-hashtag text-primary'></i> ${ctx.id}</div>
      <h3 class="text-truncate">
          <i class='fa ${icons[ctx.super_type]} text-primary'></i>
          ${ctx.name}
      </h3>
      <h4>Description</h4>
      <div class='mb-3'>${ctx.description || 'No description'}</div>
      <h4>Details</h4>
      <table class="mb-3">
          <tbody>
              <tr>
                  <td class="pe-1">TPL/PAP</td>
                  <td>${ctx.tlp} / ${ctx.pap}</td>
              </tr>
              <tr>
                  <td class="pe-1">Type</td>
                  <td class="type-or-super-type"></td>
              </tr>
              <tr>
                  <td class="pe-1">Created at</td>
                  <td><i class='nf nf-fa-calendar text-primary'></i> ${date_str(ctx.created_at)}</td>
              </tr>
              <tr>
                  <td class="pe-1">Updated at</td>
                  <td><i class='nf nf-fa-calendar text-primary'></i> ${date_str(ctx.updated_at)}</td>
              </tr>
          </tbody>
      </table>
      <h4>More actions</h4>
      <div>
        <button class="btn btn-outline-secondary" type='button' role="close">Close</button>
        <a class="btn btn-primary" href="${ctx.absolute_url}">Full details</a>
        <button class="btn btn-primary" type='button' role="edit">Quick edit</button>
      </div>
    </div>`);
  let jTypeOrSuperType;
  if (ctx.type) {
    jTypeOrSuperType = $(`<span><i class='fa nf ${styles[ctx.super_type].types[ctx.type]["icon-font-classname"]} text-primary'></i> ${styles[ctx.super_type].types[ctx.type].name}</span>`);
  }
  else {
    jTypeOrSuperType = $(`<span><i class='fa ${styles[ctx.super_type]["icon-font-classname"]} text-primary'></i> ${ctx.super_type}</span>`);
  }
  view.find('.type-or-super-type').append(jTypeOrSuperType);
  if (ctx.content) {
      let jContent = $(`<h4>Content</h4><pre>${ctx.content}</pre>`);
      view.find('table').after(jContent);
  }
  return view;
};

export const entity_relation_view = (ctx, styles) => {
    return $(`<div class='container pt-2'>
        <h5>Entity relation</h5>
        <div class="form-group mb-2">
            <label>Relation name</label>
            <input class="form-control" type="text" placeholder="Relation name" value="${ctx.name}" name="name"/>
        </div>
        <div class="mt-3">
            <button type="button" class="btn btn-outline-secondary" role="cancel">Cancel</button>
            <button type="button" class="btn btn-primary" role="save">Save</button>
        </div>
      </div>`);
};

export const entity_creation_view = (ctx, styles) => {
    let view = $(`<div class='container pt-2'>
        <h5><i class="fa ${styles[ctx.super_type]['icon-font-classname']}"></i> ${ctx.super_type} entity</h5>
        <div class="form-group mb-2">
            <label>Entity name</label>
            <input class="form-control" type="text" placeholder="Entity name" value="${ctx.name}" name="name"/>
        </div>
        <div class="optional-type"></div>
        <div class="optional-content"></div>
        <div class="mt-3 mb-2">
            <button type="button" class="btn btn-outline-secondary" role="cancel">Cancel</button>
            <button type="button" class="btn btn-primary" role="save">Save</button>
        </div>
      </div>`);

    if (styles[ctx.super_type] && Object.keys(styles[ctx.super_type].types).length !== 0) {
        let typePart = $(`<div class="form-group mb-2">
            <label>${ctx.super_type} type</label>
            <select class='form-control' name="type" size="6"></select>
        </div>`);
        view.find('.optional-type').append(typePart);

        let jOptions = [];
        for(let type in styles[ctx.super_type].types) {
            let jOption = $(`<option value="${type}"><i class="fa nf ${styles[ctx.super_type].types[type]['icon-font-classname']}"></i> ${styles[ctx.super_type].types[type]['name']}</option>`);
            if (type === ctx.type) {
                jOption.prop('selected', true);
            }
            jOptions.push(jOption);
        }
        let size = Math.min(8, jOptions.length);
        view.find('select[name=type]').attr('size', size).append(jOptions);
    }

    if (ctx.super_type === 'DataFragment') {
        let contentPart = $(`<div class="form-group mb-2">
                <label>Content</label>
                <textarea name='content' class="form-control" row="5"></textarea>
            </div>`);
        if (ctx.content) {
            contentPart.find('textarea[name=content]').val(ctx.content);
        }
        view.find('.optional-content').append(contentPart);
    }
    return view;
};
