// hr_core/static_src/js/utils/icons.js

/*
  Previously FontAwesome was loaded via CDN.
  This project uses only a small subset of icons, so we install FA via NPM and
  import only the icons we use. We then convert <i class="fa-..."> elements
  into inline SVGs on initial load and after HTMX swaps.
*/

import {dom, library} from '@fortawesome/fontawesome-svg-core';

import {faCircleXmark as faCircleXmarkRegular} from '@fortawesome/free-regular-svg-icons';

import {
  faArrowLeft,
  faBars,
  faCartPlus,
  faCartShopping,
  faCircleCheck,
  faCircleInfo,
  faCircleXmark,
  faClock,
  faEnvelope,
  faLock,
  faMapLocationDot,
  faPenToSquare as faEdit,
  faRotateRight,
  faSpinner,
  faTriangleExclamation,
  faXmark as faTimes,
} from '@fortawesome/free-solid-svg-icons';

library.add(
  faEnvelope,
  faCircleCheck,
  faTriangleExclamation,
  faCircleInfo,
  faCartPlus,
  faMapLocationDot,
  faSpinner,
  faRotateRight,
  faEdit,
  faLock,
  faArrowLeft,
  faClock,
  faCartShopping,
  faTimes,
  faBars,
  faCircleXmark,
  faCircleXmarkRegular
);

const ICON_SELECTOR = 'i.fa, i.fas, i.far, i.fab, i.fa-solid, i.fa-regular, i.fa-brands';

export function renderIcons(root = document) {
  if (root?.querySelector?.(ICON_SELECTOR)) {
    dom.i2svg({ node: root });
  }
}

// Register HTMX hook once
if (!window.__hr_fa_htmx_hooked__) {
  window.__hr_fa_htmx_hooked__ = true;

  document.body.addEventListener('htmx:afterSettle', (e) => {
    renderIcons(e.target);
  });
}
