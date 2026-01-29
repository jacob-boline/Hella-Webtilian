// hr_core/static_src/js/utils/globals.js
/**
 * @typedef  {Object}   HxDetail
 * @typedef  {Object}   HrSite
 * @typedef  {{clientSecret?: string, sessionId: string, reused?: boolean}} StripeSessionResponse
 * @typedef {{ mount: (el: Element) => void }} StripeEmbeddedCheckout
 * @typedef {{ initEmbeddedCheckout: (opts: { fetchClientSecret: () => Promise<string> }) => Promise<StripeEmbeddedCheckout> }} StripeInstance
 * @typedef {(publishableKey: string) => StripeInstance} StripeCtor
 * @property {(function(string, number=): void)=} showGlobalMessage
 * @property {(function(): void)=} openDrawer
 * @property {(function(): void)=} hideModal
 * @property {string=}  message
 * @property {string=}  text
 * @property {number=}  duration
 * @property {boolean=} close_modal
 * @property {boolean=} open_drawer
 * @property {string=}  focus
 * @property {number=}  item_count
 * @property {number=}  count
 * @property {string=}  image_url
 * @property {string=}  price
 * @property {string=}  variant_slug
*/
