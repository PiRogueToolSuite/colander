export const overlay_button = (icon, label, title) => {
  title = title || label;
  return $(`<button class="btn btn-sm btn-outline-secondary bg-light" title="${title}">
      <i class="fa ${icon}" aria-hidden="true"></i>
      <span class="label">${label}</span>
    </button>`);
};

