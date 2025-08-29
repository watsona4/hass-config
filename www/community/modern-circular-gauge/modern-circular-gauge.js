/******************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */
/* global Reflect, Promise, SuppressedError, Symbol, Iterator */


function __decorate(decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
}

typeof SuppressedError === "function" ? SuppressedError : function (error, suppressed, message) {
    var e = new Error(message);
    return e.name = "SuppressedError", e.error = error, e.suppressed = suppressed, e;
};

/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$3=globalThis,e$5=t$3.ShadowRoot&&(void 0===t$3.ShadyCSS||t$3.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$2=Symbol(),o$6=new WeakMap;let n$4 = class n{constructor(t,e,o){if(this._$cssResult$=true,o!==s$2)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$5&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=o$6.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&o$6.set(s,t));}return t}toString(){return this.cssText}};const r$5=t=>new n$4("string"==typeof t?t:t+"",void 0,s$2),i$5=(t,...e)=>{const o=1===t.length?t[0]:e.reduce(((e,s,o)=>e+(t=>{if(true===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[o+1]),t[0]);return new n$4(o,t,s$2)},S$1=(s,o)=>{if(e$5)s.adoptedStyleSheets=o.map((t=>t instanceof CSSStyleSheet?t:t.styleSheet));else for(const e of o){const o=document.createElement("style"),n=t$3.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=e.cssText,s.appendChild(o);}},c$2=e$5?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$5(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:i$4,defineProperty:e$4,getOwnPropertyDescriptor:h$1,getOwnPropertyNames:r$4,getOwnPropertySymbols:o$5,getPrototypeOf:n$3}=Object,a$1=globalThis,c$1=a$1.trustedTypes,l$1=c$1?c$1.emptyScript:"",p$1=a$1.reactiveElementPolyfillSupport,d$1=(t,s)=>t,u$1={toAttribute(t,s){switch(s){case Boolean:t=t?l$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,s){let i=t;switch(s){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t);}catch(t){i=null;}}return i}},f$1=(t,s)=>!i$4(t,s),b$1={attribute:true,type:String,converter:u$1,reflect:false,useDefault:false,hasChanged:f$1};Symbol.metadata??=Symbol("metadata"),a$1.litPropertyMetadata??=new WeakMap;let y$1 = class y extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t);}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,s=b$1){if(s.state&&(s.attribute=false),this._$Ei(),this.prototype.hasOwnProperty(t)&&((s=Object.create(s)).wrapped=true),this.elementProperties.set(t,s),!s.noAccessor){const i=Symbol(),h=this.getPropertyDescriptor(t,i,s);void 0!==h&&e$4(this.prototype,t,h);}}static getPropertyDescriptor(t,s,i){const{get:e,set:r}=h$1(this.prototype,t)??{get(){return this[s]},set(t){this[s]=t;}};return {get:e,set(s){const h=e?.call(this);r?.call(this,s),this.requestUpdate(t,h,i);},configurable:true,enumerable:true}}static getPropertyOptions(t){return this.elementProperties.get(t)??b$1}static _$Ei(){if(this.hasOwnProperty(d$1("elementProperties")))return;const t=n$3(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties);}static finalize(){if(this.hasOwnProperty(d$1("finalized")))return;if(this.finalized=true,this._$Ei(),this.hasOwnProperty(d$1("properties"))){const t=this.properties,s=[...r$4(t),...o$5(t)];for(const i of s)this.createProperty(i,t[i]);}const t=this[Symbol.metadata];if(null!==t){const s=litPropertyMetadata.get(t);if(void 0!==s)for(const[t,i]of s)this.elementProperties.set(t,i);}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const i=this._$Eu(t,s);void 0!==i&&this._$Eh.set(i,t);}this.elementStyles=this.finalizeStyles(this.styles);}static finalizeStyles(s){const i=[];if(Array.isArray(s)){const e=new Set(s.flat(1/0).reverse());for(const s of e)i.unshift(c$2(s));}else void 0!==s&&i.push(c$2(s));return i}static _$Eu(t,s){const i=s.attribute;return  false===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=false,this.hasUpdated=false,this._$Em=null,this._$Ev();}_$Ev(){this._$ES=new Promise((t=>this.enableUpdating=t)),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach((t=>t(this)));}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.();}removeController(t){this._$EO?.delete(t);}_$E_(){const t=new Map,s=this.constructor.elementProperties;for(const i of s.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t);}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return S$1(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(true),this._$EO?.forEach((t=>t.hostConnected?.()));}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach((t=>t.hostDisconnected?.()));}attributeChangedCallback(t,s,i){this._$AK(t,i);}_$ET(t,s){const i=this.constructor.elementProperties.get(t),e=this.constructor._$Eu(t,i);if(void 0!==e&&true===i.reflect){const h=(void 0!==i.converter?.toAttribute?i.converter:u$1).toAttribute(s,i.type);this._$Em=t,null==h?this.removeAttribute(e):this.setAttribute(e,h),this._$Em=null;}}_$AK(t,s){const i=this.constructor,e=i._$Eh.get(t);if(void 0!==e&&this._$Em!==e){const t=i.getPropertyOptions(e),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:u$1;this._$Em=e,this[e]=h.fromAttribute(s,t.type)??this._$Ej?.get(e)??null,this._$Em=null;}}requestUpdate(t,s,i){if(void 0!==t){const e=this.constructor,h=this[t];if(i??=e.getPropertyOptions(t),!((i.hasChanged??f$1)(h,s)||i.useDefault&&i.reflect&&h===this._$Ej?.get(t)&&!this.hasAttribute(e._$Eu(t,i))))return;this.C(t,s,i);} false===this.isUpdatePending&&(this._$ES=this._$EP());}C(t,s,{useDefault:i,reflect:e,wrapped:h},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??s??this[t]),true!==h||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(s=void 0),this._$AL.set(t,s)),true===e&&this._$Em!==t&&(this._$Eq??=new Set).add(t));}async _$EP(){this.isUpdatePending=true;try{await this._$ES;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,s]of this._$Ep)this[t]=s;this._$Ep=void 0;}const t=this.constructor.elementProperties;if(t.size>0)for(const[s,i]of t){const{wrapped:t}=i,e=this[s];true!==t||this._$AL.has(s)||void 0===e||this.C(s,void 0,i,e);}}let t=false;const s=this._$AL;try{t=this.shouldUpdate(s),t?(this.willUpdate(s),this._$EO?.forEach((t=>t.hostUpdate?.())),this.update(s)):this._$EM();}catch(s){throw t=false,this._$EM(),s}t&&this._$AE(s);}willUpdate(t){}_$AE(t){this._$EO?.forEach((t=>t.hostUpdated?.())),this.hasUpdated||(this.hasUpdated=true,this.firstUpdated(t)),this.updated(t);}_$EM(){this._$AL=new Map,this.isUpdatePending=false;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return  true}update(t){this._$Eq&&=this._$Eq.forEach((t=>this._$ET(t,this[t]))),this._$EM();}updated(t){}firstUpdated(t){}};y$1.elementStyles=[],y$1.shadowRootOptions={mode:"open"},y$1[d$1("elementProperties")]=new Map,y$1[d$1("finalized")]=new Map,p$1?.({ReactiveElement:y$1}),(a$1.reactiveElementVersions??=[]).push("2.1.0");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$2=globalThis,i$3=t$2.trustedTypes,s$1=i$3?i$3.createPolicy("lit-html",{createHTML:t=>t}):void 0,e$3="$lit$",h=`lit$${Math.random().toFixed(9).slice(2)}$`,o$4="?"+h,n$2=`<${o$4}>`,r$3=document,l=()=>r$3.createComment(""),c=t=>null===t||"object"!=typeof t&&"function"!=typeof t,a=Array.isArray,u=t=>a(t)||"function"==typeof t?.[Symbol.iterator],d="[ \t\n\f\r]",f=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,v=/-->/g,_=/>/g,m=RegExp(`>|${d}(?:([^\\s"'>=/]+)(${d}*=${d}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),p=/'/g,g=/"/g,$=/^(?:script|style|textarea|title)$/i,y=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),x=y(1),b=y(2),T=Symbol.for("lit-noChange"),E=Symbol.for("lit-nothing"),A=new WeakMap,C=r$3.createTreeWalker(r$3,129);function P(t,i){if(!a(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==s$1?s$1.createHTML(i):i}const V=(t,i)=>{const s=t.length-1,o=[];let r,l=2===i?"<svg>":3===i?"<math>":"",c=f;for(let i=0;i<s;i++){const s=t[i];let a,u,d=-1,y=0;for(;y<s.length&&(c.lastIndex=y,u=c.exec(s),null!==u);)y=c.lastIndex,c===f?"!--"===u[1]?c=v:void 0!==u[1]?c=_:void 0!==u[2]?($.test(u[2])&&(r=RegExp("</"+u[2],"g")),c=m):void 0!==u[3]&&(c=m):c===m?">"===u[0]?(c=r??f,d=-1):void 0===u[1]?d=-2:(d=c.lastIndex-u[2].length,a=u[1],c=void 0===u[3]?m:'"'===u[3]?g:p):c===g||c===p?c=m:c===v||c===_?c=f:(c=m,r=void 0);const x=c===m&&t[i+1].startsWith("/>")?" ":"";l+=c===f?s+n$2:d>=0?(o.push(a),s.slice(0,d)+e$3+s.slice(d)+h+x):s+h+(-2===d?i:x);}return [P(t,l+(t[s]||"<?>")+(2===i?"</svg>":3===i?"</math>":"")),o]};class N{constructor({strings:t,_$litType$:s},n){let r;this.parts=[];let c=0,a=0;const u=t.length-1,d=this.parts,[f,v]=V(t,s);if(this.el=N.createElement(f,n),C.currentNode=this.el.content,2===s||3===s){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes);}for(;null!==(r=C.nextNode())&&d.length<u;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(e$3)){const i=v[a++],s=r.getAttribute(t).split(h),e=/([.?@])?(.*)/.exec(i);d.push({type:1,index:c,name:e[2],strings:s,ctor:"."===e[1]?H:"?"===e[1]?I:"@"===e[1]?L:k}),r.removeAttribute(t);}else t.startsWith(h)&&(d.push({type:6,index:c}),r.removeAttribute(t));if($.test(r.tagName)){const t=r.textContent.split(h),s=t.length-1;if(s>0){r.textContent=i$3?i$3.emptyScript:"";for(let i=0;i<s;i++)r.append(t[i],l()),C.nextNode(),d.push({type:2,index:++c});r.append(t[s],l());}}}else if(8===r.nodeType)if(r.data===o$4)d.push({type:2,index:c});else {let t=-1;for(;-1!==(t=r.data.indexOf(h,t+1));)d.push({type:7,index:c}),t+=h.length-1;}c++;}}static createElement(t,i){const s=r$3.createElement("template");return s.innerHTML=t,s}}function S(t,i,s=t,e){if(i===T)return i;let h=void 0!==e?s._$Co?.[e]:s._$Cl;const o=c(i)?void 0:i._$litDirective$;return h?.constructor!==o&&(h?._$AO?.(false),void 0===o?h=void 0:(h=new o(t),h._$AT(t,s,e)),void 0!==e?(s._$Co??=[])[e]=h:s._$Cl=h),void 0!==h&&(i=S(t,h._$AS(t,i.values),h,e)),i}class M{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:i},parts:s}=this._$AD,e=(t?.creationScope??r$3).importNode(i,true);C.currentNode=e;let h=C.nextNode(),o=0,n=0,l=s[0];for(;void 0!==l;){if(o===l.index){let i;2===l.type?i=new R(h,h.nextSibling,this,t):1===l.type?i=new l.ctor(h,l.name,l.strings,this,t):6===l.type&&(i=new z(h,this,t)),this._$AV.push(i),l=s[++n];}o!==l?.index&&(h=C.nextNode(),o++);}return C.currentNode=r$3,e}p(t){let i=0;for(const s of this._$AV) void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}}class R{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,i,s,e){this.type=2,this._$AH=E,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cv=e?.isConnected??true;}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t?.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=S(this,t,i),c(t)?t===E||null==t||""===t?(this._$AH!==E&&this._$AR(),this._$AH=E):t!==this._$AH&&t!==T&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):u(t)?this.k(t):this._(t);}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}_(t){this._$AH!==E&&c(this._$AH)?this._$AA.nextSibling.data=t:this.T(r$3.createTextNode(t)),this._$AH=t;}$(t){const{values:i,_$litType$:s}=t,e="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=N.createElement(P(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===e)this._$AH.p(i);else {const t=new M(e,this),s=t.u(this.options);t.p(i),this.T(s),this._$AH=t;}}_$AC(t){let i=A.get(t.strings);return void 0===i&&A.set(t.strings,i=new N(t)),i}k(t){a(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const h of t)e===i.length?i.push(s=new R(this.O(l()),this.O(l()),this,this.options)):s=i[e],s._$AI(h),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,i){for(this._$AP?.(false,true,i);t&&t!==this._$AB;){const i=t.nextSibling;t.remove(),t=i;}}setConnected(t){ void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t));}}class k{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,i,s,e,h){this.type=1,this._$AH=E,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=h,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=E;}_$AI(t,i=this,s,e){const h=this.strings;let o=false;if(void 0===h)t=S(this,t,i,0),o=!c(t)||t!==this._$AH&&t!==T,o&&(this._$AH=t);else {const e=t;let n,r;for(t=h[0],n=0;n<h.length-1;n++)r=S(this,e[s+n],i,n),r===T&&(r=this._$AH[n]),o||=!c(r)||r!==this._$AH[n],r===E?t=E:t!==E&&(t+=(r??"")+h[n+1]),this._$AH[n]=r;}o&&!e&&this.j(t);}j(t){t===E?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"");}}class H extends k{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===E?void 0:t;}}class I extends k{constructor(){super(...arguments),this.type=4;}j(t){this.element.toggleAttribute(this.name,!!t&&t!==E);}}class L extends k{constructor(t,i,s,e,h){super(t,i,s,e,h),this.type=5;}_$AI(t,i=this){if((t=S(this,t,i,0)??E)===T)return;const s=this._$AH,e=t===E&&s!==E||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,h=t!==E&&(s===E||e);e&&this.element.removeEventListener(this.name,this,s),h&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t);}}class z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){S(this,t);}}const j=t$2.litHtmlPolyfillSupport;j?.(N,R),(t$2.litHtmlVersions??=[]).push("3.3.0");const B=(t,i,s)=>{const e=s?.renderBefore??i;let h=e._$litPart$;if(void 0===h){const t=s?.renderBefore??null;e._$litPart$=h=new R(i.insertBefore(l(),t),t,void 0,s??{});}return h._$AI(t),h};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const s=globalThis;let i$2 = class i extends y$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const r=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=B(r,this.renderRoot,this.renderOptions);}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(true);}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(false);}render(){return T}};i$2._$litElement$=true,i$2["finalized"]=true,s.litElementHydrateSupport?.({LitElement:i$2});const o$3=s.litElementPolyfillSupport;o$3?.({LitElement:i$2});(s.litElementVersions??=[]).push("4.2.0");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1=t=>(e,o)=>{ void 0!==o?o.addInitializer((()=>{customElements.define(t,e);})):customElements.define(t,e);};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const o$2={attribute:true,type:String,converter:u$1,reflect:false,hasChanged:f$1},r$2=(t=o$2,e,r)=>{const{kind:n,metadata:i}=r;let s=globalThis.litPropertyMetadata.get(i);if(void 0===s&&globalThis.litPropertyMetadata.set(i,s=new Map),"setter"===n&&((t=Object.create(t)).wrapped=true),s.set(r.name,t),"accessor"===n){const{name:o}=r;return {set(r){const n=e.get.call(this);e.set.call(this,r),this.requestUpdate(o,n,t);},init(e){return void 0!==e&&this.C(o,void 0,t,e),e}}}if("setter"===n){const{name:o}=r;return function(r){const n=this[o];e.call(this,r),this.requestUpdate(o,n,t);}}throw Error("Unsupported decorator location: "+n)};function n$1(t){return (e,o)=>"object"==typeof o?r$2(t,e,o):((t,e,o)=>{const r=e.hasOwnProperty(o);return e.constructor.createProperty(o,t),r?Object.getOwnPropertyDescriptor(e,o):void 0})(t,e,o)}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function r$1(r){return n$1({...r,state:true,attribute:false})}

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const e$2=(e,t,c)=>(c.configurable=true,c.enumerable=true,Reflect.decorate&&"object"!=typeof t&&Object.defineProperty(e,t,c),c);

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
function r(r){return (n,e)=>e$2(n,e,{async get(){return await this.updateComplete,this.renderRoot?.querySelector(r)??null}})}

function hasAction(config){return config!==undefined&&config.action!=="none";}

const DEFAULT_MIN=0;const DEFAULT_MAX=100;const MAX_ANGLE$1=270;const RADIUS$1=47;const INNER_RADIUS=42;const TERTIARY_RADIUS=37;const NUMBER_ENTITY_DOMAINS=["sensor","number","counter","input_number"];

const rgbToHex=rgb=>{if(!rgb)return "";return "#".concat(rgb.map(x=>x.toString(16).padStart(2,"0")).join(""));};const hexToRgb=hex=>{if(!hex.startsWith("#"))return hex;hex=hex.replace("#","");return [parseInt(hex.substring(0,2),16),parseInt(hex.substring(2,4),16),parseInt(hex.substring(4,6),16)];};const interpolateColor=(from,to,percentage)=>{if(from===to){return from;}let fromColor=from;let toColor=to;if(!from.startsWith("#")){fromColor=colourNameToHex(from);}if(!to.startsWith("#")){toColor=colourNameToHex(to);}const fromColorRgb=hexToRgb(fromColor);const toColorRgb=hexToRgb(toColor);const q=1-percentage;const red=Math.round(fromColorRgb[0]*q+toColorRgb[0]*percentage);const green=Math.round(fromColorRgb[1]*q+toColorRgb[1]*percentage);const blue=Math.round(fromColorRgb[2]*q+toColorRgb[2]*percentage);return rgbToHex([red,green,blue]);};const colourNameToHex=color=>{const colors={"aliceblue":"#f0f8ff","antiquewhite":"#faebd7","aqua":"#00ffff","aquamarine":"#7fffd4","azure":"#f0ffff","beige":"#f5f5dc","bisque":"#ffe4c4","black":"#000000","blanchedalmond":"#ffebcd","blue":"#0000ff","blueviolet":"#8a2be2","brown":"#a52a2a","burlywood":"#deb887","cadetblue":"#5f9ea0","chartreuse":"#7fff00","chocolate":"#d2691e","coral":"#ff7f50","cornflowerblue":"#6495ed","cornsilk":"#fff8dc","crimson":"#dc143c","cyan":"#00ffff","darkblue":"#00008b","darkcyan":"#008b8b","darkgoldenrod":"#b8860b","darkgray":"#a9a9a9","darkgreen":"#006400","darkkhaki":"#bdb76b","darkmagenta":"#8b008b","darkolivegreen":"#556b2f","darkorange":"#ff8c00","darkorchid":"#9932cc","darkred":"#8b0000","darksalmon":"#e9967a","darkseagreen":"#8fbc8f","darkslateblue":"#483d8b","darkslategray":"#2f4f4f","darkturquoise":"#00ced1","darkviolet":"#9400d3","deeppink":"#ff1493","deepskyblue":"#00bfff","dimgray":"#696969","dodgerblue":"#1e90ff","firebrick":"#b22222","floralwhite":"#fffaf0","forestgreen":"#228b22","fuchsia":"#ff00ff","gainsboro":"#dcdcdc","ghostwhite":"#f8f8ff","gold":"#ffd700","goldenrod":"#daa520","gray":"#808080","green":"#008000","greenyellow":"#adff2f","honeydew":"#f0fff0","hotpink":"#ff69b4","indianred ":"#cd5c5c","indigo":"#4b0082","ivory":"#fffff0","khaki":"#f0e68c","lavender":"#e6e6fa","lavenderblush":"#fff0f5","lawngreen":"#7cfc00","lemonchiffon":"#fffacd","lightblue":"#add8e6","lightcoral":"#f08080","lightcyan":"#e0ffff","lightgoldenrodyellow":"#fafad2","lightgrey":"#d3d3d3","lightgreen":"#90ee90","lightpink":"#ffb6c1","lightsalmon":"#ffa07a","lightseagreen":"#20b2aa","lightskyblue":"#87cefa","lightslategray":"#778899","lightsteelblue":"#b0c4de","lightyellow":"#ffffe0","lime":"#00ff00","limegreen":"#32cd32","linen":"#faf0e6","magenta":"#ff00ff","maroon":"#800000","mediumaquamarine":"#66cdaa","mediumblue":"#0000cd","mediumorchid":"#ba55d3","mediumpurple":"#9370d8","mediumseagreen":"#3cb371","mediumslateblue":"#7b68ee","mediumspringgreen":"#00fa9a","mediumturquoise":"#48d1cc","mediumvioletred":"#c71585","midnightblue":"#191970","mintcream":"#f5fffa","mistyrose":"#ffe4e1","moccasin":"#ffe4b5","navajowhite":"#ffdead","navy":"#000080","oldlace":"#fdf5e6","olive":"#808000","olivedrab":"#6b8e23","orange":"#ffa500","orangered":"#ff4500","orchid":"#da70d6","palegoldenrod":"#eee8aa","palegreen":"#98fb98","paleturquoise":"#afeeee","palevioletred":"#d87093","papayawhip":"#ffefd5","peachpuff":"#ffdab9","peru":"#cd853f","pink":"#ffc0cb","plum":"#dda0dd","powderblue":"#b0e0e6","purple":"#800080","rebeccapurple":"#663399","red":"#ff0000","rosybrown":"#bc8f8f","royalblue":"#4169e1","saddlebrown":"#8b4513","salmon":"#fa8072","sandybrown":"#f4a460","seagreen":"#2e8b57","seashell":"#fff5ee","sienna":"#a0522d","silver":"#c0c0c0","skyblue":"#87ceeb","slateblue":"#6a5acd","slategray":"#708090","snow":"#fffafa","springgreen":"#00ff7f","steelblue":"#4682b4","tan":"#d2b48c","teal":"#008080","thistle":"#d8bfd8","tomato":"#ff6347","turquoise":"#40e0d0","violet":"#ee82ee","wheat":"#f5deb3","white":"#ffffff","whitesmoke":"#f5f5f5","yellow":"#ffff00","yellowgreen":"#9acd32"};if(typeof colors[color.toLowerCase()]!='undefined')return colors[color.toLowerCase()];return "#000000";};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t={ATTRIBUTE:1},e$1=t=>(...e)=>({_$litDirective$:t,values:e});let i$1 = class i{constructor(t){}get _$AU(){return this._$AM._$AU}_$AT(t,e,i){this._$Ct=t,this._$AM=e,this._$Ci=i;}_$AS(t,e){return this.update(t,e)}update(t,e){return this.render(...e)}};

/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const n="important",i=" !"+n,o$1=e$1(class extends i$1{constructor(t$1){if(super(t$1),t$1.type!==t.ATTRIBUTE||"style"!==t$1.name||t$1.strings?.length>2)throw Error("The `styleMap` directive must be used in the `style` attribute and must be the only part in the attribute.")}render(t){return Object.keys(t).reduce(((e,r)=>{const s=t[r];return null==s?e:e+`${r=r.includes("-")?r:r.replace(/(?:^(webkit|moz|ms|o)|)(?=[A-Z])/g,"-$&").toLowerCase()}:${s};`}),"")}update(e,[r]){const{style:s}=e.element;if(void 0===this.ft)return this.ft=new Set(Object.keys(r)),this.render(r);for(const t of this.ft)null==r[t]&&(this.ft.delete(t),t.includes("-")?s.removeProperty(t):s[t]=null);for(const t in r){const e=r[t];if(null!=e){this.ft.add(t);const r="string"==typeof e&&e.endsWith(i);t.includes("-")||r?s.setProperty(t,r?e.slice(0,-11):e,r?n:""):s[t]=e;}}return T}});

/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const o=o=>o??E;

const rotateVector=([[a,b],[c,d]],[x,y])=>[a*x+b*y,c*x+d*y];const createRotateMatrix=x=>[[Math.cos(x),-Math.sin(x)],[Math.sin(x),Math.cos(x)]];const addVector=([a1,a2],[b1,b2])=>[a1+b1,a2+b2];const toRadian=angle=>angle/180*Math.PI;const clamp=(value,min,max)=>Math.min(Math.max(value,min),max);const svgArc=options=>{const{x,y,r,start,end,rotate=0}=options;const cx=x;const cy=y;const rx=r;const ry=r;const t1=toRadian(start);const t2=toRadian(end);const delta=(t2-t1)%(2*Math.PI);const phi=toRadian(rotate);const rotMatrix=createRotateMatrix(phi);const[sX,sY]=addVector(rotateVector(rotMatrix,[rx*Math.cos(t1),ry*Math.sin(t1)]),[cx,cy]);const[eX,eY]=addVector(rotateVector(rotMatrix,[rx*Math.cos(t1+delta),ry*Math.sin(t1+delta)]),[cx,cy]);const fA=delta>Math.PI?1:0;const fS=delta>0?1:0;return ["M",sX,sY,"A",rx,ry,phi/(2*Math.PI)*360,fA,fS,eX,eY].join(" ");};const strokeDashArc=(from,to,min,max,radius)=>{const start=valueToPercentage(from,min,max);const end=valueToPercentage(to,min,max);const track=radius*2*Math.PI*MAX_ANGLE$1/360;const arc=Math.max((end-start)*track,0);const arcOffset=start*track-0.5;const strokeDasharray=`${arc} ${track-arc}`;const strokeDashOffset=`-${arcOffset}`;return [strokeDasharray,strokeDashOffset];};const getAngle=(value,min,max)=>{return valueToPercentage(isNaN(value)?min:value,min,max)*MAX_ANGLE$1;};const valueToPercentage=(value,min,max)=>{return (clamp(value,min,max)-min)/(max-min);};const currentDashArc=(value,min,max,radius,startFromZero)=>{if(startFromZero){return strokeDashArc(value>0?0:value,value>0?value:0,min,max,radius);}else {return strokeDashArc(min,value,min,max,radius);}};function renderPath(pathClass,d,strokeDash=undefined,style=undefined){return b`
    <path
      class="${pathClass}"
      d=${d}
      stroke-dasharray=${o(strokeDash?strokeDash[0]:undefined)}
      stroke-dashoffset=${o(strokeDash?strokeDash[1]:undefined)}
      style=${o(style)}
    />`;}function renderColorSegments(segments,min,max,radius,smooth_segments){if(smooth_segments){return renderSegmentsGradient(segments,min,max);}else {return renderSegments(segments,min,max,radius);}}function renderSegmentsGradient(segments,min,max){if(segments){let sortedSegments=[...segments].sort((a,b)=>Number(a.from)-Number(b.from));let gradient="";sortedSegments.map((segment,index)=>{const angle=getAngle(Number(segment.from),min,max)+45;const color=typeof segment.color==="object"?rgbToHex(segment.color):segment.color;gradient+=`${color} ${angle}deg${index!=sortedSegments.length-1?",":""}`;});return [b`
      <foreignObject x="-50" y="-50" width="100%" height="100%" overflow="visible" transform="rotate(45)">
        <div style="width: 110px; height: 110px; margin-left: -5px; margin-top: -5px; background-image: conic-gradient(${gradient})">
        </div>
      </foreignObject>
    `];}return [];}function renderSegments(segments,min,max,radius){if(segments){let sortedSegments=[...segments].sort((a,b)=>Number(a.from)-Number(b.from));return [...sortedSegments].map((segment,index)=>{let roundEnd;const startAngle=index===0?0:getAngle(Number(segment.from),min,max);const angle=index===sortedSegments.length-1?MAX_ANGLE$1:getAngle(Number(sortedSegments[index+1].from),min,max);const color=typeof segment.color==="object"?rgbToHex(segment.color):segment.color;const segmentPath=svgArc({x:0,y:0,start:startAngle,end:angle,r:radius});if(index===0||index===sortedSegments.length-1){const endPath=svgArc({x:0,y:0,start:index===0?0:MAX_ANGLE$1,end:index===0?0:MAX_ANGLE$1,r:radius});roundEnd=renderPath("segment",endPath,undefined,o$1({"stroke":color,"stroke-linecap":"round"}));}return b`${roundEnd}
        ${renderPath("segment",segmentPath,undefined,o$1({"stroke":color}))}
      `;});}return [];}function computeSegments(numberState,segments,smooth_segments,element){if(segments){let sortedSegments=[...segments].sort((a,b)=>Number(a.from)-Number(b.from));for(let i=0;i<sortedSegments.length;i++){let segment=sortedSegments[i];if(segment&&(numberState>=Number(segment.from)||i===0)&&(i+1==(sortedSegments===null||sortedSegments===void 0?void 0:sortedSegments.length)||numberState<Number(sortedSegments[i+1].from))){if(smooth_segments){let color=typeof segment.color==="object"?rgbToHex(segment.color):segment.color;if(color.includes("var(--")&&element){color=getComputedStyle(element).getPropertyValue(color.replace(/(var\()|(\))/g,"").trim());}const nextSegment=sortedSegments[i+1]?sortedSegments[i+1]:segment;let nextColor=typeof nextSegment.color==="object"?rgbToHex(nextSegment.color):nextSegment.color;if(nextColor.includes("var(--")&&element){nextColor=getComputedStyle(element).getPropertyValue(nextColor.replace(/(var\()|(\))/g,"").trim());}return interpolateColor(color,nextColor,valueToPercentage(numberState,Number(segment.from),Number(nextSegment.from)));}else {const color=typeof segment.color==="object"?rgbToHex(segment.color):segment.color;return color;}}}}return undefined;}

function registerCustomCard(params){const windowWithCards=window;windowWithCards.customCards=windowWithCards.customCards||[];windowWithCards.customCards.push(Object.assign(Object.assign({},params),{preview:true,documentationURL:`https://github.com/selvalt7/modern-circular-gauge`}));}

const fireEvent=(node,type,detail,options)=>{options=options||{};detail=detail===null||detail===undefined?{}:detail;const event=new Event(type,{bubbles:options.bubbles===undefined?true:options.bubbles,cancelable:Boolean(options.cancelable),composed:options.composed===undefined?true:options.composed});event.detail=detail;node.dispatchEvent(event);return event;};

const handleAction=async(node,_hass,config,action)=>{fireEvent(node,"hass-action",{config,action});};

/**
 * @license
 * Copyright 2018 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const e=e$1(class extends i$1{constructor(t$1){if(super(t$1),t$1.type!==t.ATTRIBUTE||"class"!==t$1.name||t$1.strings?.length>2)throw Error("`classMap()` can only be used in the `class` attribute and must be the only part in the attribute.")}render(t){return " "+Object.keys(t).filter((s=>t[s])).join(" ")+" "}update(s,[i]){if(void 0===this.st){this.st=new Set,void 0!==s.strings&&(this.nt=new Set(s.strings.join(" ").split(/\s/).filter((t=>""!==t))));for(const t in i)i[t]&&!this.nt?.has(t)&&this.st.add(t);return this.render(i)}const r=s.element.classList;for(const t of this.st)t in i||(r.remove(t),this.st.delete(t));for(const t in i){const s=!!i[t];s===this.st.has(t)||this.nt?.has(t)||(s?(r.add(t),this.st.add(t)):(r.remove(t),this.st.delete(t)));}return T}});

const getActionHandler=()=>{const body=document.body;if(body.querySelector("action-handler")){return body.querySelector("action-handler");}const actionhandler=document.createElement("action-handler");body.appendChild(actionhandler);return actionhandler;};const actionHandlerBind=(element,options)=>{const actionhandler=getActionHandler();if(!actionhandler){return;}actionhandler.bind(element,options);};const actionHandler=e$1(class extends i$1{update(part,[options]){actionHandlerBind(part.element,options);return T;}render(_options){}});

const subscribeRenderTemplate=(conn,onChange,params)=>conn.subscribeMessage(msg=>onChange(msg),Object.assign({type:"render_template"},params));

const isTemplateRegex=/{%|{{/;const isTemplate=value=>isTemplateRegex.test(value);

let ModernCircularGaugeElement=class ModernCircularGaugeElement extends i$2{constructor(){super(...arguments);this.min=DEFAULT_MIN;this.max=DEFAULT_MAX;this.value=0;this.radius=47;this.maxAngle=MAX_ANGLE$1;this.smoothSegments=false;this.needle=false;this.startFromZero=false;this.outter=false;this._updated=false;}connectedCallback(){super.connectedCallback();if(!this._updated){this._path=svgArc({x:0,y:0,start:0,end:this.maxAngle,r:this.radius});this._rotateAngle=360-this.maxAngle/2-90;this._updated=true;}}render(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3;if(!this._path){return E;}if(this.outter){const current=strokeDashArc(this.value,this.value,this.min,this.max,this.radius);return x`
      <svg viewBox="-50 -50 100 100" preserveAspectRatio="xMidYMid"
        overflow="visible"
        style=${o$1({"--gauge-stroke-width":((_a=this.foregroundStyle)===null||_a===void 0?void 0:_a.width)?`${(_b=this.foregroundStyle)===null||_b===void 0?void 0:_b.width}px`:undefined,"--gauge-color":((_c=this.foregroundStyle)===null||_c===void 0?void 0:_c.color)&&((_d=this.foregroundStyle)===null||_d===void 0?void 0:_d.color)!="adaptive"?(_e=this.foregroundStyle)===null||_e===void 0?void 0:_e.color:computeSegments(this.value,this.segments,this.smoothSegments,this)})}
      >
        <g transform="rotate(${this._rotateAngle})">
          ${!((_f=this.foregroundStyle)===null||_f===void 0?void 0:_f.color)?renderPath("dot border",this._path,current,o$1({"opacity":(_h=(_g=this.foregroundStyle)===null||_g===void 0?void 0:_g.opacity)!==null&&_h!==void 0?_h:1,"stroke-width":(_j=this.foregroundStyle)===null||_j===void 0?void 0:_j.width})):E}
          ${renderPath("dot",this._path,current,o$1({"opacity":(_l=(_k=this.foregroundStyle)===null||_k===void 0?void 0:_k.opacity)!==null&&_l!==void 0?_l:1,"stroke":(_m=this.foregroundStyle)===null||_m===void 0?void 0:_m.color,"stroke-width":(_o=this.foregroundStyle)===null||_o===void 0?void 0:_o.width}))}
        </g>
      </svg>
      `;}else {const current=this.needle?undefined:currentDashArc(this.value,this.min,this.max,this.radius,this.startFromZero);const needle=this.needle?strokeDashArc(this.value,this.value,this.min,this.max,this.radius):undefined;return x`
        <svg viewBox="-50 -50 100 100" preserveAspectRatio="xMidYMid"
          overflow="visible"
          style=${o$1({"--gauge-stroke-width":((_p=this.foregroundStyle)===null||_p===void 0?void 0:_p.width)?`${(_q=this.foregroundStyle)===null||_q===void 0?void 0:_q.width}px`:undefined,"--gauge-color":((_r=this.foregroundStyle)===null||_r===void 0?void 0:_r.color)&&((_s=this.foregroundStyle)===null||_s===void 0?void 0:_s.color)!="adaptive"?(_t=this.foregroundStyle)===null||_t===void 0?void 0:_t.color:computeSegments(this.value,this.segments,this.smoothSegments,this)})}
        >
          <g transform="rotate(${this._rotateAngle})">
            <defs>
              <mask id="needle-border-mask">
                <rect x="-70" y="-70" width="140" height="140" fill="white"/>
                ${needle?b`
                <path
                  class="needle-border"
                  d=${this._path}
                  stroke-dasharray="${needle[0]}"
                  stroke-dashoffset="${needle[1]}"
                  stroke="black"
                />
                `:E}
              </mask>
              <mask id="gradient-path">
                ${renderPath("arc",this._path,undefined,o$1({"stroke":"white","stroke-width":((_u=this.backgroundStyle)===null||_u===void 0?void 0:_u.width)?`${(_v=this.backgroundStyle)===null||_v===void 0?void 0:_v.width}px`:undefined}))}
              </mask>
              <mask id="gradient-current-path">
                ${current?renderPath("arc current",this._path,current,o$1({"stroke":"white","visibility":this.value<=this.min&&this.min>=0?"hidden":"visible"})):E}
              </mask>
            </defs>
            <g class="background" mask=${o(needle?"url(#needle-border-mask)":undefined)} style=${o$1({"opacity":(_w=this.backgroundStyle)===null||_w===void 0?void 0:_w.opacity,"--gauge-stroke-width":((_x=this.backgroundStyle)===null||_x===void 0?void 0:_x.width)?`${(_y=this.backgroundStyle)===null||_y===void 0?void 0:_y.width}px`:undefined})}>
              ${renderPath("arc clear",this._path,undefined,o$1({"stroke":((_z=this.backgroundStyle)===null||_z===void 0?void 0:_z.color)&&this.backgroundStyle.color!="adaptive"?this.backgroundStyle.color:undefined}))}
              ${this.segments&&(needle||((_0=this.backgroundStyle)===null||_0===void 0?void 0:_0.color)=="adaptive")?b`
              <g class="segments" mask=${o(this.smoothSegments?"url(#gradient-path)":undefined)}>
                ${renderColorSegments(this.segments,this.min,this.max,this.radius,this.smoothSegments)}
              </g>`:E}
            </g>
            ${current?((_1=this.foregroundStyle)===null||_1===void 0?void 0:_1.color)=="adaptive"&&this.segments?b`
            <g class="foreground-segments" mask="url(#gradient-current-path)" style=${o$1({"opacity":(_2=this.foregroundStyle)===null||_2===void 0?void 0:_2.opacity})}>
              ${renderColorSegments(this.segments,this.min,this.max,this.radius,this.smoothSegments)}
            </g>
            `:renderPath("arc current",this._path,current,o$1({"visibility":this.value<=this.min&&this.min>=0?"hidden":"visible","opacity":(_3=this.foregroundStyle)===null||_3===void 0?void 0:_3.opacity})):E}
            ${needle?b`
            ${renderPath("needle",this._path,needle)}
            `:E}
          </g>
        </svg>
      `;}}static get styles(){return i$5`
    :host {
      --gauge-primary-color: var(--light-blue-color);

      --gauge-color: var(--gauge-primary-color);
      --gauge-stroke-width: 6px;
    }
    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    g {
      fill: none;
    }
    .arc {
      fill: none;
      stroke-linecap: round;
      stroke-width: var(--gauge-stroke-width);
    }

    .arc.clear {
      stroke: var(--primary-background-color);
    }

    .arc.current {
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    .segment {
      fill: none;
      stroke-width: var(--gauge-stroke-width);
    }

    .segments {
      opacity: 0.45;
    }

    .needle {
      fill: none;
      stroke-linecap: round;
      stroke-width: var(--gauge-stroke-width);
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    .needle-border {
      fill: none;
      stroke-linecap: round;
      stroke-width: calc(var(--gauge-stroke-width) + 4px);
      transition: all 1s ease 0s, stroke 0.3s ease-out;
    }
    
    .dot {
      fill: none;
      stroke-linecap: round;
      stroke-width: calc(var(--gauge-stroke-width) / 2);
      stroke: var(--primary-text-color);
      transition: all 1s ease 0s;
    }

    .dot.border {
      stroke: var(--gauge-color);
      stroke-width: var(--gauge-stroke-width);
    }
    `;}};__decorate([n$1({type:Number})],ModernCircularGaugeElement.prototype,"min",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeElement.prototype,"max",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeElement.prototype,"value",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeElement.prototype,"radius",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeElement.prototype,"maxAngle",void 0);__decorate([n$1({type:Array})],ModernCircularGaugeElement.prototype,"segments",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeElement.prototype,"smoothSegments",void 0);__decorate([n$1({type:Object})],ModernCircularGaugeElement.prototype,"foregroundStyle",void 0);__decorate([n$1({type:Object})],ModernCircularGaugeElement.prototype,"backgroundStyle",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeElement.prototype,"needle",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeElement.prototype,"startFromZero",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeElement.prototype,"outter",void 0);__decorate([r$1()],ModernCircularGaugeElement.prototype,"_updated",void 0);__decorate([r$1()],ModernCircularGaugeElement.prototype,"_path",void 0);__decorate([r$1()],ModernCircularGaugeElement.prototype,"_rotateAngle",void 0);ModernCircularGaugeElement=__decorate([t$1("modern-circular-gauge-element")],ModernCircularGaugeElement);

var NumberFormat;(function(NumberFormat){NumberFormat["language"]="language";NumberFormat["system"]="system";NumberFormat["comma_decimal"]="comma_decimal";NumberFormat["decimal_comma"]="decimal_comma";NumberFormat["space_comma"]="space_comma";NumberFormat["none"]="none";})(NumberFormat||(NumberFormat={}));var TimeFormat;(function(TimeFormat){TimeFormat["language"]="language";TimeFormat["system"]="system";TimeFormat["am_pm"]="12";TimeFormat["twenty_four"]="24";})(TimeFormat||(TimeFormat={}));var TimeZone;(function(TimeZone){TimeZone["local"]="local";TimeZone["server"]="server";})(TimeZone||(TimeZone={}));var DateFormat;(function(DateFormat){DateFormat["language"]="language";DateFormat["system"]="system";DateFormat["DMY"]="DMY";DateFormat["MDY"]="MDY";DateFormat["YMD"]="YMD";})(DateFormat||(DateFormat={}));var FirstWeekday;(function(FirstWeekday){FirstWeekday["language"]="language";FirstWeekday["monday"]="monday";FirstWeekday["tuesday"]="tuesday";FirstWeekday["wednesday"]="wednesday";FirstWeekday["thursday"]="thursday";FirstWeekday["friday"]="friday";FirstWeekday["saturday"]="saturday";FirstWeekday["sunday"]="sunday";})(FirstWeekday||(FirstWeekday={}));

const numberFormatToLocale=localeOptions=>{switch(localeOptions.number_format){case NumberFormat.comma_decimal:return ["en-US","en"];case NumberFormat.decimal_comma:return ["de","es","it"];case NumberFormat.space_comma:return ["fr","sv","cs"];case NumberFormat.system:return undefined;default:return localeOptions.language;}};const round=(value,precision=2)=>Math.round(value*10**precision)/10**precision;const formatNumber=(num,localeOptions,options)=>{const locale=localeOptions?numberFormatToLocale(localeOptions):undefined;Number.isNaN=Number.isNaN||function isNaN(input){return typeof input==="number"&&isNaN(input);};if((localeOptions===null||localeOptions===void 0?void 0:localeOptions.number_format)!==NumberFormat.none&&!Number.isNaN(Number(num))){return new Intl.NumberFormat(locale,getDefaultFormatOptions(num,options)).format(Number(num));}if(!Number.isNaN(Number(num))&&num!==""&&(localeOptions===null||localeOptions===void 0?void 0:localeOptions.number_format)===NumberFormat.none){return new Intl.NumberFormat("en-US",getDefaultFormatOptions(num,Object.assign(Object.assign({},options),{useGrouping:false}))).format(Number(num));}if(typeof num==="string"){return num;}return `${round(num,options===null||options===void 0?void 0:options.maximumFractionDigits).toString()}${(options===null||options===void 0?void 0:options.style)==="currency"?` ${options.currency}`:""}`;};const getNumberFormatOptions=(entityState,entity)=>{var _a;const precision=entity===null||entity===void 0?void 0:entity.display_precision;if(precision!=null){return {maximumFractionDigits:precision,minimumFractionDigits:precision};}if(Number.isInteger(Number((_a=entityState===null||entityState===void 0?void 0:entityState.attributes)===null||_a===void 0?void 0:_a.step))&&Number.isInteger(Number(entityState===null||entityState===void 0?void 0:entityState.state))){return {maximumFractionDigits:0};}return undefined;};const getDefaultFormatOptions=(num,options)=>{const defaultOptions=Object.assign({maximumFractionDigits:2},options);if(typeof num!=="string"){return defaultOptions;}if(!options||options.minimumFractionDigits===undefined&&options.maximumFractionDigits===undefined){const digits=num.indexOf(".")>-1?num.split(".")[1].length:0;defaultOptions.minimumFractionDigits=digits;defaultOptions.maximumFractionDigits=digits;}return defaultOptions;};

let ModernCircularGaugeState=class ModernCircularGaugeState extends i$2{constructor(){super(...arguments);this.showUnit=true;this.small=false;this.stateMargin=82;this._updated=false;}firstUpdated(_changedProperties){this._updated=true;this._scaleText();}updated(_changedProperties){super.updated(_changedProperties);if(!this._updated){return;}this._scaleText();}_computeState(){var _a,_b,_c,_d,_e;if(!this.stateObj&&this.stateOverride!==undefined){return this.stateOverride;}if(this.stateObj){const state=(_a=this.stateOverride)!==null&&_a!==void 0?_a:this.stateObj.state;const attributes=(_b=this.stateObj.attributes)!==null&&_b!==void 0?_b:undefined;const entityState=Number.isNaN(state)?state:formatNumber(state,(_c=this.hass)===null||_c===void 0?void 0:_c.locale,getNumberFormatOptions({state,attributes},(_d=this.hass)===null||_d===void 0?void 0:_d.entities[(_e=this.stateObj)===null||_e===void 0?void 0:_e.entity_id]));return entityState;}return "";}_scaleText(){var _a;const svgRoot=this.shadowRoot.querySelector(".state");if(!svgRoot){return;}const svgText=svgRoot.querySelector("text");const bbox=svgText.getBBox();const maxWidth=this.stateMargin-Math.abs((_a=this.verticalOffset)!==null&&_a!==void 0?_a:0)*0.5;if(bbox.width>maxWidth){const scale=maxWidth/bbox.width;if(this.verticalOffset){svgText.setAttribute("transform",`translate(0 ${this.verticalOffset}) scale(${scale}) translate(0 ${-this.verticalOffset})`);}else {svgText.setAttribute("transform",`scale(${scale})`);}}else {svgText.removeAttribute("transform");}}render(){var _a;if(!this.hass||!this.stateObj&&this.stateOverride===undefined){return x``;}const state=this._computeState();const verticalOffset=(_a=this.verticalOffset)!==null&&_a!==void 0?_a:0;return x`
    <svg class="state ${e({"small":this.small})}" overflow="visible" viewBox="-50 -50 100 100">
      <text x="0" y=${verticalOffset} class="value">
        ${state}
        ${this.showUnit?this.small?this.unit:b`
        <tspan class="unit" dx=${ -4} dy=${ -6}>${this.unit}</tspan>
        `:E}
      </text>
      <text class="state-label" style=${o$1({"font-size":this.labelFontSize?`${this.labelFontSize}px`:undefined})} y=${verticalOffset+(this.small?9*Math.sign(verticalOffset):13)}>
        ${this.label}
      </text>
    </svg>
    `;}static get styles(){return i$5`
    :host {
      --state-text-color: var(--primary-text-color);
      --state-font-size: 24px;
      --state-pointer-events: auto;

      pointer-events: none;
    }

    :host(.preview) {
      --state-pointer-events: none;
    }

    svg {
      width: 100%;
      height: 100%;
      display: block;
      pointer-events: none;
    }

    .state {
      text-anchor: middle;
    }

    .value {
      font-size: var(--state-font-size-override, var(--state-font-size));
      fill: var(--state-text-color-override, var(--state-text-color));
      dominant-baseline: middle;
      pointer-events: var(--state-pointer-events);
    }

    .unit {
      font-size: .33em;
      opacity: 0.6;
    }

    .small {
      --state-text-color: var(--state-text-color-override, var(--secondary-text-color));
    }

    .small .unit {
      opacity: 1;
      font-size: inherit;
    }

    .small .value {
      --state-font-size: 10px;
      fill: var(--state-text-color);
    }

    .state-label {
      font-size: 0.49em;
      fill: var(--secondary-text-color);
      dominant-baseline: middle;
    }
    `;}};__decorate([n$1({attribute:false})],ModernCircularGaugeState.prototype,"hass",void 0);__decorate([n$1({type:Object})],ModernCircularGaugeState.prototype,"stateObj",void 0);__decorate([n$1()],ModernCircularGaugeState.prototype,"unit",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeState.prototype,"showUnit",void 0);__decorate([n$1()],ModernCircularGaugeState.prototype,"label",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeState.prototype,"labelFontSize",void 0);__decorate([n$1({type:Boolean})],ModernCircularGaugeState.prototype,"small",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeState.prototype,"verticalOffset",void 0);__decorate([n$1()],ModernCircularGaugeState.prototype,"stateOverride",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeState.prototype,"stateMargin",void 0);__decorate([r$1()],ModernCircularGaugeState.prototype,"_updated",void 0);ModernCircularGaugeState=__decorate([t$1("modern-circular-gauge-state")],ModernCircularGaugeState);

const ICONPOSITIONS=[-3.6,-4.8,-5.52,-12];const ICONSIZES=[0.12,0.12,0.18,0.3];let ModernCircularGaugeIcon=class ModernCircularGaugeIcon extends i$2{constructor(){super(...arguments);this.position=2;this._updated=false;}firstUpdated(_changedProperties){super.firstUpdated(_changedProperties);}updated(_changedProperties){super.updated(_changedProperties);if(this._updated){return;}this._haStateIcon.then(async haStateIcon=>{if(!haStateIcon.shadowRoot){return;}this._getSvgFromHaStateIcon(haStateIcon);if(!this._updated){const observer=new MutationObserver(()=>{this._getSvgFromHaStateIcon(haStateIcon);observer.disconnect();});observer.observe(haStateIcon.shadowRoot,{childList:true,subtree:true});}});}_getSvgFromHaStateIcon(haStateIconEl){var _a,_b;const haIcon=(_a=haStateIconEl.shadowRoot)===null||_a===void 0?void 0:_a.querySelector('ha-icon');if(!haIcon){return;}(_b=haIcon===null||haIcon===void 0?void 0:haIcon.updateComplete)===null||_b===void 0?void 0:_b.then(()=>{var _a,_b;const haSvgIcon=(_a=haIcon===null||haIcon===void 0?void 0:haIcon.shadowRoot)===null||_a===void 0?void 0:_a.querySelector('ha-svg-icon');const svg=(_b=haSvgIcon===null||haSvgIcon===void 0?void 0:haSvgIcon.shadowRoot)===null||_b===void 0?void 0:_b.querySelector('svg');if(svg){const gaugeIcon=this.shadowRoot.querySelector('.gauge-icon-group');const iconGroup=svg.querySelector('g');if(gaugeIcon&&iconGroup){gaugeIcon.appendChild(iconGroup);this._updated=true;}}});}_computeIconPosition(){if(this.iconVerticalPositionOverride!==undefined){return this.iconVerticalPositionOverride*24*-0.01;}return ICONPOSITIONS[this.position];}_computeIconSize(){if(this.iconSizeOverride!==undefined){return this.iconSizeOverride*0.01;}return ICONSIZES[this.position];}render(){return x`
    <ha-state-icon
      .hass=${this.hass}
      .stateObj=${this.stateObj}
      .icon=${this.icon}
    ></ha-state-icon>
    <svg class="gauge-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <g class="gauge-icon-group" transform="translate(0 12) translate(0 ${this._computeIconPosition()}) translate(12 12) scale(${this._computeIconSize()}) translate(-12 -12)">
      </g>
    </svg>`;}};ModernCircularGaugeIcon.styles=i$5`
    :host {
      width: 100%;
      height: 100%;
      fill: var(--icon-primary-color, currentcolor);
    }

    svg {
      width: 100%;
      height: 100%;
      display: block;
    }

    path.primary-path {
      opacity: var(--icon-primary-opactity, 1);
    }
    path.secondary-path {
      fill: var(--icon-secondary-color, currentcolor);
      opacity: var(--icon-secondary-opactity, 0.5);
    }

    ha-state-icon {
      visibility: hidden;
      position: absolute;
    }
  `;__decorate([n$1({attribute:false})],ModernCircularGaugeIcon.prototype,"hass",void 0);__decorate([n$1({attribute:false})],ModernCircularGaugeIcon.prototype,"stateObj",void 0);__decorate([n$1()],ModernCircularGaugeIcon.prototype,"icon",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeIcon.prototype,"position",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeIcon.prototype,"iconVerticalPositionOverride",void 0);__decorate([n$1({type:Number})],ModernCircularGaugeIcon.prototype,"iconSizeOverride",void 0);__decorate([r('ha-state-icon')],ModernCircularGaugeIcon.prototype,"_haStateIcon",void 0);__decorate([r$1()],ModernCircularGaugeIcon.prototype,"_updated",void 0);ModernCircularGaugeIcon=__decorate([t$1("modern-circular-gauge-icon")],ModernCircularGaugeIcon);

const ROTATE_ANGLE$1=360-MAX_ANGLE$1/2-90;const path$1=svgArc({x:0,y:0,start:0,end:MAX_ANGLE$1,r:RADIUS$1});svgArc({x:0,y:0,start:0,end:MAX_ANGLE$1,r:INNER_RADIUS});svgArc({x:0,y:0,start:0,end:MAX_ANGLE$1,r:TERTIARY_RADIUS});registerCustomCard({type:"modern-circular-gauge",name:"Modern Circular Gauge",description:"Modern circular gauge"});let ModernCircularGauge=class ModernCircularGauge extends i$2{constructor(){super(...arguments);this._hasSecondary=false;this._templateResults={};this._unsubRenderTemplates=new Map();}static async getConfigElement(){await Promise.resolve().then(function () { return mcgEditor; });return document.createElement("modern-circular-gauge-editor");}static async getStubConfig(hass){const entities=Object.keys(hass.states);const numbers=entities.filter(e=>NUMBER_ENTITY_DOMAINS.includes(e.split(".")[0]));return {type:"custom:modern-circular-gauge",entity:numbers[0]};}setConfig(config){if(!config.entity){throw new Error("Entity must be specified");}let secondary=config.secondary;if(secondary===undefined&&config.secondary_entity!==undefined){secondary=config.secondary_entity;}if(typeof secondary==="object"){const template=secondary.template||"";if(template.length>0){secondary=template;}let secondaryGaugeForegroundStyle=secondary.gauge_foreground_style;if(!secondaryGaugeForegroundStyle){if(secondary.gauge_width!==undefined){secondaryGaugeForegroundStyle={width:secondary.gauge_width};secondary=Object.assign(Object.assign({},secondary),{gauge_foreground_style:secondaryGaugeForegroundStyle});}}}let gaugeForegroundStyle=config.gauge_foreground_style;if(!gaugeForegroundStyle){if(config.gauge_width!==undefined){gaugeForegroundStyle={width:config.gauge_width};config=Object.assign(Object.assign({},config),{gauge_foreground_style:gaugeForegroundStyle});}}this._config=Object.assign(Object.assign({min:DEFAULT_MIN,max:DEFAULT_MAX,show_header:true,show_state:true},config),{secondary:secondary,secondary_entity:undefined});}connectedCallback(){var _a;super.connectedCallback();this._inCardPicker=(_a=this.parentElement)===null||_a===void 0?void 0:_a.classList.contains("preview");this._tryConnect();}disconnectedCallback(){super.disconnectedCallback();this._tryDisconnect();}firstUpdated(_changedProperties){this._stateMargin=this._calcStateMargin();}updated(changedProps){super.updated(changedProps);if(!this._config||!this.hass){return;}this._tryConnect();}_hasCardAction(){var _a,_b,_c,_d;return !((_a=this._config)===null||_a===void 0?void 0:_a.tap_action)||hasAction((_b=this._config)===null||_b===void 0?void 0:_b.tap_action)||hasAction((_c=this._config)===null||_c===void 0?void 0:_c.hold_action)||hasAction((_d=this._config)===null||_d===void 0?void 0:_d.double_tap_action);}render(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3,_4,_5,_6,_7,_8,_9,_10,_11,_12,_13,_14,_15,_16,_17,_18,_19,_20,_21,_22,_23,_24,_25;if(!this.hass||!this._config){return x``;}const stateObj=this.hass.states[this._config.entity];const templatedState=(_b=(_a=this._templateResults)===null||_a===void 0?void 0:_a.entity)===null||_b===void 0?void 0:_b.result;if(!stateObj&&templatedState===undefined){if(isTemplate(this._config.entity)){return this._renderWarning();}else {return this._renderWarning(this._config.entity,"",undefined,"mdi:help");}}const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);const icon=(_e=(_d=(_c=this._templateResults)===null||_c===void 0?void 0:_c.icon)===null||_d===void 0?void 0:_d.result)!==null&&_e!==void 0?_e:this._config.icon;if((stateObj===null||stateObj===void 0?void 0:stateObj.state)==="unavailable"){return this._renderWarning((_k=(_j=(_h=(_g=(_f=this._templateResults)===null||_f===void 0?void 0:_f.name)===null||_g===void 0?void 0:_g.result)!==null&&_h!==void 0?_h:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_j!==void 0?_j:stateObj.attributes.friendly_name)!==null&&_k!==void 0?_k:'',this.hass.localize("state.default.unavailable"),stateObj,icon);}if(isNaN(numberState)){return this._renderWarning((_q=(_p=(_o=(_m=(_l=this._templateResults)===null||_l===void 0?void 0:_l.name)===null||_m===void 0?void 0:_m.result)!==null&&_o!==void 0?_o:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_p!==void 0?_p:stateObj.attributes.friendly_name)!==null&&_q!==void 0?_q:'',"NaN",stateObj,icon);}const attributes=(_r=stateObj===null||stateObj===void 0?void 0:stateObj.attributes)!==null&&_r!==void 0?_r:undefined;const unit=(_s=this._config.unit)!==null&&_s!==void 0?_s:stateObj===null||stateObj===void 0?void 0:stateObj.attributes.unit_of_measurement;const min=Number((_v=(_u=(_t=this._templateResults)===null||_t===void 0?void 0:_t.min)===null||_u===void 0?void 0:_u.result)!==null&&_v!==void 0?_v:this._config.min)||DEFAULT_MIN;const max=Number((_y=(_x=(_w=this._templateResults)===null||_w===void 0?void 0:_w.max)===null||_x===void 0?void 0:_x.result)!==null&&_y!==void 0?_y:this._config.max)||DEFAULT_MAX;const stateOverride=(_1=(_0=(_z=this._templateResults)===null||_z===void 0?void 0:_z.stateText)===null||_0===void 0?void 0:_0.result)!==null&&_1!==void 0?_1:isTemplate(String(this._config.state_text))?"":this._config.state_text||undefined;const iconCenter=!((_2=this._config.show_state)!==null&&_2!==void 0?_2:false)&&((_3=this._config.show_icon)!==null&&_3!==void 0?_3:true);const segments=(_6=(_5=(_4=this._templateResults)===null||_4===void 0?void 0:_4.segments)===null||_5===void 0?void 0:_5.result)!==null&&_6!==void 0?_6:this._config.segments;const segmentsLabel=this._getSegmentLabel(numberState,segments);return x`
    <ha-card
      class="${e({"flex-column-reverse":this._config.header_position=="top","action":this._hasCardAction(),"icon-center":iconCenter})}"
      @action=${this._handleAction}
      .actionHandler=${actionHandler({hasHold:hasAction(this._config.hold_action),hasDoubleClick:hasAction(this._config.double_tap_action)})}
      tabindex=${o(!this._config.tap_action||hasAction(this._config.tap_action)?"0":undefined)}
    >
      ${this._config.show_header?x`
      <div class="header" style=${o$1({"--gauge-header-font-size":this._config.header_font_size?`${this._config.header_font_size}px`:undefined,"transform":this._config.header_offset?`translate(0, ${this._config.header_offset}px)`:undefined})}>
        <p class="name">
          ${(_10=(_9=(_8=(_7=this._templateResults)===null||_7===void 0?void 0:_7.name)===null||_8===void 0?void 0:_8.result)!==null&&_9!==void 0?_9:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_10!==void 0?_10:attributes?attributes.friendly_name:""}
        </p>
      </div>
      `:E}
      <div
        class="container${e({"dual-gauge":typeof this._config.secondary!="string"&&((_11=this._config.secondary)===null||_11===void 0?void 0:_11.show_gauge)=="inner"})}"
        style=${o$1({"--gauge-color":((_12=this._config.gauge_foreground_style)===null||_12===void 0?void 0:_12.color)&&((_13=this._config.gauge_foreground_style)===null||_13===void 0?void 0:_13.color)!="adaptive"?(_14=this._config.gauge_foreground_style)===null||_14===void 0?void 0:_14.color:computeSegments(numberState,segments,this._config.smooth_segments,this)})}
      >
        <div class="gauge-container">
          <modern-circular-gauge-element
            .min=${min}
            .max=${max}
            .value=${numberState}
            .radius=${(_15=this._config.gauge_radius)!==null&&_15!==void 0?_15:RADIUS$1}
            .maxAngle=${MAX_ANGLE$1}
            .segments=${segments}
            .smoothSegments=${this._config.smooth_segments}
            .foregroundStyle=${this._config.gauge_foreground_style}
            .backgroundStyle=${this._config.gauge_background_style}
            .needle=${this._config.needle}
            .startFromZero=${this._config.start_from_zero}
          ></modern-circular-gauge-element>
          ${typeof this._config.secondary!="string"?((_16=this._config.secondary)===null||_16===void 0?void 0:_16.show_gauge)&&((_17=this._config.secondary)===null||_17===void 0?void 0:_17.show_gauge)!="none"?this._renderSecondaryGauge():E:E}
          ${typeof this._config.tertiary!="string"?((_18=this._config.tertiary)===null||_18===void 0?void 0:_18.show_gauge)&&((_19=this._config.tertiary)===null||_19===void 0?void 0:_19.show_gauge)!="none"?this._renderTertiaryRing():E:E}
        </div>
        <div class="gauge-state">
          ${this._config.show_state?x`
          <modern-circular-gauge-state
            class=${e({"preview":this._inCardPicker})}
            style=${o$1({"--state-text-color":this._config.adaptive_state_color?"var(--gauge-color)":undefined,"--state-font-size-override":this._config.state_font_size?`${this._config.state_font_size}px`:undefined})}
            .hass=${this.hass}
            .stateObj=${stateObj}
            .stateOverride=${(_20=segmentsLabel||stateOverride)!==null&&_20!==void 0?_20:templatedState}
            .unit=${unit}
            .verticalOffset=${typeof this._config.secondary!="string"&&((_21=this._config.secondary)===null||_21===void 0?void 0:_21.state_size)=="big"?-14:0}
            .label=${typeof this._config.secondary!="string"&&((_22=this._config.secondary)===null||_22===void 0?void 0:_22.state_size)=="big"?(_23=this._config)===null||_23===void 0?void 0:_23.label:""}
            .stateMargin=${this._stateMargin}
            .labelFontSize=${this._config.label_font_size}
            .showUnit=${(_24=this._config.show_unit)!==null&&_24!==void 0?_24:true}
          ></modern-circular-gauge-state>
          `:E}
          ${this._renderSecondaryState()}
          ${this._renderTertiaryState()}
        </div>
        ${((_25=this._config.show_icon)!==null&&_25!==void 0?_25:true)?this._renderIcon(icon):E}
      </div> 
    </ha-card>
    `;}_renderWarning(headerText,stateText,stateObj,icon){var _a,_b,_c,_d,_e,_f,_g;const iconCenter=(stateText===null||stateText===void 0?void 0:stateText.length)==0;return x`
      <ha-card
      class="${e({"flex-column-reverse":((_a=this._config)===null||_a===void 0?void 0:_a.header_position)=="top","action":this._hasCardAction()&&stateObj!==undefined})}"
      @action=${o(stateObj?this._handleAction:undefined)}
      .actionHandler=${actionHandler({hasHold:hasAction((_b=this._config)===null||_b===void 0?void 0:_b.hold_action),hasDoubleClick:hasAction((_c=this._config)===null||_c===void 0?void 0:_c.double_tap_action)})}
      tabindex=${o(!((_d=this._config)===null||_d===void 0?void 0:_d.tap_action)||hasAction((_e=this._config)===null||_e===void 0?void 0:_e.tap_action)?"0":undefined)}
      >
      <div class="header" style=${o$1({"--gauge-header-font-size":((_f=this._config)===null||_f===void 0?void 0:_f.header_font_size)?`${this._config.header_font_size}px`:undefined,"transform":((_g=this._config)===null||_g===void 0?void 0:_g.header_offset)?`translate(0, ${this._config.header_offset}px)`:undefined})}>
        <p class="name">
          ${headerText}
        </p>
      </div>
      <div class=${e({"icon-center":iconCenter,"container":true})}>
        <svg viewBox="-50 -50 100 100" preserveAspectRatio="xMidYMid"
          overflow="visible"
        >
          <g transform="rotate(${ROTATE_ANGLE$1})">
            ${renderPath("arc clear",path$1)}
          </g>
        </svg>
        <modern-circular-gauge-state
          .hass=${this.hass}
          .stateOverride=${stateText}
        ></modern-circular-gauge-state>
        <modern-circular-gauge-icon
          class="warning-icon"
          .hass=${this.hass}
          .stateObj=${stateObj}
          .icon=${icon}
          .position=${iconCenter?3:2}
        ></modern-circular-gauge-icon>
      </div>
      </ha-card>
      `;}_renderIcon(iconOverride){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3,_4,_5,_6,_7;const iconEntity=(_a=this._config)===null||_a===void 0?void 0:_a.icon_entity;let entityId;let templatedState;let segments;let gaugeForegroundStyle;if(!iconEntity||iconEntity==="primary"){entityId=(_b=this._config)===null||_b===void 0?void 0:_b.entity;templatedState=(_d=(_c=this._templateResults)===null||_c===void 0?void 0:_c.entity)===null||_d===void 0?void 0:_d.result;segments=(_g=(_f=(_e=this._templateResults)===null||_e===void 0?void 0:_e.segments)===null||_f===void 0?void 0:_f.result)!==null&&_g!==void 0?_g:(_h=this._config)===null||_h===void 0?void 0:_h.segments;gaugeForegroundStyle=(_j=this._config)===null||_j===void 0?void 0:_j.gauge_foreground_style;}else if(typeof((_k=this._config)===null||_k===void 0?void 0:_k.secondary)==="object"&&iconEntity==="secondary"){entityId=this._config.secondary.entity;templatedState=(_m=(_l=this._templateResults)===null||_l===void 0?void 0:_l.secondaryEntity)===null||_m===void 0?void 0:_m.result;segments=(_q=(_p=(_o=this._templateResults)===null||_o===void 0?void 0:_o.secondarySegments)===null||_p===void 0?void 0:_p.result)!==null&&_q!==void 0?_q:this._config.secondary.segments;gaugeForegroundStyle=this._config.secondary.gauge_foreground_style;}else if(typeof((_r=this._config)===null||_r===void 0?void 0:_r.tertiary)==="object"&&iconEntity==="tertiary"){entityId=this._config.tertiary.entity;templatedState=(_t=(_s=this._templateResults)===null||_s===void 0?void 0:_s.tertiaryEntity)===null||_t===void 0?void 0:_t.result;segments=(_w=(_v=(_u=this._templateResults)===null||_u===void 0?void 0:_u.tertiarySegments)===null||_v===void 0?void 0:_v.result)!==null&&_w!==void 0?_w:this._config.tertiary.segments;gaugeForegroundStyle=this._config.tertiary.gauge_foreground_style;}const stateObj=this.hass.states[entityId||""];if(!stateObj&&templatedState===undefined){return x``;}const value=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);const iconCenter=!((_y=(_x=this._config)===null||_x===void 0?void 0:_x.show_state)!==null&&_y!==void 0?_y:false)&&((_0=(_z=this._config)===null||_z===void 0?void 0:_z.show_icon)!==null&&_0!==void 0?_0:true);const secondaryHasLabel=typeof((_1=this._config)===null||_1===void 0?void 0:_1.secondary)!="string"&&((_3=(_2=this._config)===null||_2===void 0?void 0:_2.secondary)===null||_3===void 0?void 0:_3.label);const iconPosition=iconCenter?3:secondaryHasLabel&&this._hasSecondary?0:this._hasSecondary?1:2;return x`
    <modern-circular-gauge-icon
      class=${e({"adaptive":!!((_4=this._config)===null||_4===void 0?void 0:_4.adaptive_icon_color)})}
      style=${o$1({"--gauge-color":(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.color)&&gaugeForegroundStyle.color!="adaptive"?gaugeForegroundStyle.color:computeSegments(value,segments,(_5=this._config)===null||_5===void 0?void 0:_5.smooth_segments,this)})}
      .hass=${this.hass}
      .stateObj=${stateObj}
      .icon=${iconOverride}
      .position=${iconPosition}
      .iconVerticalPositionOverride=${(_6=this._config)===null||_6===void 0?void 0:_6.icon_vertical_position}
      .iconSizeOverride=${(_7=this._config)===null||_7===void 0?void 0:_7.icon_size}
    ></modern-circular-gauge-icon>
    `;}_calcStateMargin(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s;let gauges=[];if(typeof((_a=this._config)===null||_a===void 0?void 0:_a.secondary)!="string"){if(((_c=(_b=this._config)===null||_b===void 0?void 0:_b.secondary)===null||_c===void 0?void 0:_c.show_gauge)=="inner"){const gauge={radius:(_d=this._config.secondary.gauge_radius)!==null&&_d!==void 0?_d:INNER_RADIUS,width:(_f=(_e=this._config.secondary.gauge_foreground_style)===null||_e===void 0?void 0:_e.width)!==null&&_f!==void 0?_f:4};gauges.push(gauge);}}if(typeof((_g=this._config)===null||_g===void 0?void 0:_g.tertiary)!="string"){if(((_j=(_h=this._config)===null||_h===void 0?void 0:_h.tertiary)===null||_j===void 0?void 0:_j.show_gauge)=="inner"){const gauge={radius:(_k=this._config.tertiary.gauge_radius)!==null&&_k!==void 0?_k:TERTIARY_RADIUS,width:(_m=(_l=this._config.tertiary.gauge_foreground_style)===null||_l===void 0?void 0:_l.width)!==null&&_m!==void 0?_m:4};gauges.push(gauge);}}gauges.push({radius:(_p=(_o=this._config)===null||_o===void 0?void 0:_o.gauge_radius)!==null&&_p!==void 0?_p:RADIUS$1,width:(_s=(_r=(_q=this._config)===null||_q===void 0?void 0:_q.gauge_foreground_style)===null||_r===void 0?void 0:_r.width)!==null&&_s!==void 0?_s:gauges.length>1?4:6});const gauge=gauges.reduce((r,e)=>r.radius<e.radius?r:e);return (gauge.radius-gauge.width)*2;}_renderTertiaryRing(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y;const tertiaryObj=(_a=this._config)===null||_a===void 0?void 0:_a.tertiary;const stateObj=this.hass.states[tertiaryObj.entity||""];const templatedState=(_c=(_b=this._templateResults)===null||_b===void 0?void 0:_b.tertiaryEntity)===null||_c===void 0?void 0:_c.result;if(!tertiaryObj){return x``;}if(tertiaryObj.show_gauge=="inner"){if(!stateObj&&templatedState===undefined){return x`
        <modern-circular-gauge-element
          class="tertiary"
          .radius=${TERTIARY_RADIUS}
          .maxAngle=${MAX_ANGLE$1}
        ></modern-circular-gauge-element>
        `;}const min=Number((_f=(_e=(_d=this._templateResults)===null||_d===void 0?void 0:_d.tertiaryMin)===null||_e===void 0?void 0:_e.result)!==null&&_f!==void 0?_f:tertiaryObj.min)||DEFAULT_MIN;const max=Number((_j=(_h=(_g=this._templateResults)===null||_g===void 0?void 0:_g.tertiaryMax)===null||_h===void 0?void 0:_h.result)!==null&&_j!==void 0?_j:tertiaryObj.max)||DEFAULT_MAX;const segments=(_l=(_k=this._templateResults)===null||_k===void 0?void 0:_k.tertiarySegments)!==null&&_l!==void 0?_l:tertiaryObj.segments;const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);return x`
      <modern-circular-gauge-element
        class="tertiary"
        .min=${min}
        .max=${max}
        .value=${numberState}
        .radius=${(_m=tertiaryObj.gauge_radius)!==null&&_m!==void 0?_m:TERTIARY_RADIUS}
        .maxAngle=${MAX_ANGLE$1}
        .segments=${segments}
        .smoothSegments=${(_o=this._config)===null||_o===void 0?void 0:_o.smooth_segments}
        .foregroundStyle=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.gauge_foreground_style}
        .backgroundStyle=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.gauge_background_style}
        .needle=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.needle}
        .startFromZero=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.start_from_zero}
      ></modern-circular-gauge-element>
      `;}else {if(!stateObj&&templatedState===undefined){return x``;}const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);if((stateObj===null||stateObj===void 0?void 0:stateObj.state)==="unavailable"&&templatedState){return x``;}if(isNaN(numberState)){return x``;}const min=Number((_r=(_q=(_p=this._templateResults)===null||_p===void 0?void 0:_p.min)===null||_q===void 0?void 0:_q.result)!==null&&_r!==void 0?_r:(_s=this._config)===null||_s===void 0?void 0:_s.min)||DEFAULT_MIN;const max=Number((_v=(_u=(_t=this._templateResults)===null||_t===void 0?void 0:_t.max)===null||_u===void 0?void 0:_u.result)!==null&&_v!==void 0?_v:(_w=this._config)===null||_w===void 0?void 0:_w.max)||DEFAULT_MAX;return x`
      <modern-circular-gauge-element
        class="tertiary"
        .min=${min}
        .max=${max}
        .value=${numberState}
        .radius=${(_y=(_x=this._config)===null||_x===void 0?void 0:_x.gauge_radius)!==null&&_y!==void 0?_y:RADIUS$1}
        .maxAngle=${MAX_ANGLE$1}
        .foregroundStyle=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.gauge_foreground_style}
        .backgroundStyle=${tertiaryObj===null||tertiaryObj===void 0?void 0:tertiaryObj.gauge_background_style}
        .outter=${true}
      ></modern-circular-gauge-element>
      `;}}_renderSecondaryGauge(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y;const secondaryObj=(_a=this._config)===null||_a===void 0?void 0:_a.secondary;const stateObj=this.hass.states[secondaryObj.entity||""];const templatedState=(_c=(_b=this._templateResults)===null||_b===void 0?void 0:_b.secondaryEntity)===null||_c===void 0?void 0:_c.result;if(!secondaryObj){return x``;}if(secondaryObj.show_gauge=="inner"){if(!stateObj&&templatedState===undefined){return x`
        <modern-circular-gauge-element
          class="secondary"
          .radius=${INNER_RADIUS}
          .maxAngle=${MAX_ANGLE$1}
        ></modern-circular-gauge-element>
        `;}const min=Number((_f=(_e=(_d=this._templateResults)===null||_d===void 0?void 0:_d.secondaryMin)===null||_e===void 0?void 0:_e.result)!==null&&_f!==void 0?_f:secondaryObj.min)||DEFAULT_MIN;const max=Number((_j=(_h=(_g=this._templateResults)===null||_g===void 0?void 0:_g.secondaryMax)===null||_h===void 0?void 0:_h.result)!==null&&_j!==void 0?_j:secondaryObj.max)||DEFAULT_MAX;const segments=(_l=(_k=this._templateResults)===null||_k===void 0?void 0:_k.secondarySegments)!==null&&_l!==void 0?_l:secondaryObj.segments;const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);return x`
      <modern-circular-gauge-element
        class="secondary"
        .min=${min}
        .max=${max}
        .value=${numberState}
        .radius=${(_m=secondaryObj.gauge_radius)!==null&&_m!==void 0?_m:INNER_RADIUS}
        .maxAngle=${MAX_ANGLE$1}
        .segments=${segments}
        .smoothSegments=${(_o=this._config)===null||_o===void 0?void 0:_o.smooth_segments}
        .foregroundStyle=${secondaryObj===null||secondaryObj===void 0?void 0:secondaryObj.gauge_foreground_style}
        .backgroundStyle=${secondaryObj===null||secondaryObj===void 0?void 0:secondaryObj.gauge_background_style}
        .needle=${secondaryObj===null||secondaryObj===void 0?void 0:secondaryObj.needle}
        .startFromZero=${secondaryObj.start_from_zero}
      ></modern-circular-gauge-element>
      `;}else {if(!stateObj&&templatedState===undefined){return x``;}const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);if((stateObj===null||stateObj===void 0?void 0:stateObj.state)==="unavailable"&&templatedState){return x``;}if(isNaN(numberState)){return x``;}const min=Number((_r=(_q=(_p=this._templateResults)===null||_p===void 0?void 0:_p.min)===null||_q===void 0?void 0:_q.result)!==null&&_r!==void 0?_r:(_s=this._config)===null||_s===void 0?void 0:_s.min)||DEFAULT_MIN;const max=Number((_v=(_u=(_t=this._templateResults)===null||_t===void 0?void 0:_t.max)===null||_u===void 0?void 0:_u.result)!==null&&_v!==void 0?_v:(_w=this._config)===null||_w===void 0?void 0:_w.max)||DEFAULT_MAX;return x`
      <modern-circular-gauge-element
        class="secondary"
        .min=${min}
        .max=${max}
        .value=${numberState}
        .radius=${(_y=(_x=this._config)===null||_x===void 0?void 0:_x.gauge_radius)!==null&&_y!==void 0?_y:RADIUS$1}
        .maxAngle=${MAX_ANGLE$1}
        .foregroundStyle=${secondaryObj===null||secondaryObj===void 0?void 0:secondaryObj.gauge_foreground_style}
        .backgroundStyle=${secondaryObj===null||secondaryObj===void 0?void 0:secondaryObj.gauge_background_style}
        .outter=${true}
      ></modern-circular-gauge-element>
      `;}}_renderSecondaryState(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3,_4,_5;const secondary=(_a=this._config)===null||_a===void 0?void 0:_a.secondary;if(!secondary){return x``;}const iconCenter=!((_c=(_b=this._config)===null||_b===void 0?void 0:_b.show_state)!==null&&_c!==void 0?_c:false)&&((_e=(_d=this._config)===null||_d===void 0?void 0:_d.show_icon)!==null&&_e!==void 0?_e:true);if(typeof secondary==="string"){this._hasSecondary=true;return x`
      <modern-circular-gauge-state
        class=${e({"preview":this._inCardPicker})}
        .hass=${this.hass}
        .stateOverride=${(_h=(_g=(_f=this._templateResults)===null||_f===void 0?void 0:_f.secondary)===null||_g===void 0?void 0:_g.result)!==null&&_h!==void 0?_h:secondary}
        .verticalOffset=${17}
        .stateMargin=${this._stateMargin}
        small
      ></modern-circular-gauge-state>
      `;}if(!((_j=secondary.show_state)!==null&&_j!==void 0?_j:true)){return x``;}const stateObj=this.hass.states[secondary.entity||""];const templatedState=(_l=(_k=this._templateResults)===null||_k===void 0?void 0:_k.secondaryEntity)===null||_l===void 0?void 0:_l.result;if(!stateObj&&templatedState===undefined){return x``;}this._hasSecondary=true;const attributes=(_m=stateObj===null||stateObj===void 0?void 0:stateObj.attributes)!==null&&_m!==void 0?_m:undefined;const unit=(_o=secondary.unit)!==null&&_o!==void 0?_o:attributes===null||attributes===void 0?void 0:attributes.unit_of_measurement;const state=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);const stateOverride=(_r=(_q=(_p=this._templateResults)===null||_p===void 0?void 0:_p.secondaryStateText)===null||_q===void 0?void 0:_q.result)!==null&&_r!==void 0?_r:isTemplate(String(secondary.state_text))?"":secondary.state_text||undefined;const segments=(_u=(_t=(_s=this._templateResults)===null||_s===void 0?void 0:_s.secondarySegments)===null||_t===void 0?void 0:_t.result)!==null&&_u!==void 0?_u:secondary.segments;const segmentsLabel=this._getSegmentLabel(state,segments);let secondaryColor;if(secondary.adaptive_state_color){if(secondary.show_gauge=="outter"){secondaryColor=computeSegments(state,(_x=(_w=(_v=this._templateResults)===null||_v===void 0?void 0:_v.segments)===null||_w===void 0?void 0:_w.result)!==null&&_x!==void 0?_x:(_y=this._config)===null||_y===void 0?void 0:_y.segments,(_z=this._config)===null||_z===void 0?void 0:_z.smooth_segments,this);}else {secondaryColor=computeSegments(state,segments,(_0=this._config)===null||_0===void 0?void 0:_0.smooth_segments,this);}if(((_1=secondary.gauge_foreground_style)===null||_1===void 0?void 0:_1.color)&&((_2=secondary.gauge_foreground_style)===null||_2===void 0?void 0:_2.color)!="adaptive"){secondaryColor=(_3=secondary.gauge_foreground_style)===null||_3===void 0?void 0:_3.color;}}return x`
    <modern-circular-gauge-state
      @action=${this._handleSecondaryAction}
      .actionHandler=${actionHandler({hasHold:hasAction(secondary.hold_action),hasDoubleClick:hasAction(secondary.double_tap_action)})}
      class=${e({"preview":this._inCardPicker})}
      style=${o$1({"--state-text-color-override":secondaryColor!==null&&secondaryColor!==void 0?secondaryColor:secondary.state_size=="big"?"var(--secondary-text-color)":undefined,"--state-font-size-override":secondary.state_font_size?`${secondary.state_font_size}px`:undefined})}
      .hass=${this.hass}
      .stateObj=${stateObj}
      .stateOverride=${(_4=segmentsLabel||stateOverride)!==null&&_4!==void 0?_4:templatedState}
      .unit=${unit}
      .verticalOffset=${secondary.state_size=="big"?14:iconCenter?22:17}
      .small=${secondary.state_size!="big"}
      .label=${secondary.label}
      .stateMargin=${this._stateMargin}
      .labelFontSize=${secondary.label_font_size}
      .showUnit=${(_5=secondary.show_unit)!==null&&_5!==void 0?_5:true}
    ></modern-circular-gauge-state>
    `;}_renderTertiaryState(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3,_4;const tertiary=(_a=this._config)===null||_a===void 0?void 0:_a.tertiary;if(!tertiary){return x``;}if(typeof tertiary==="string"){return x`
      <modern-circular-gauge-state
        class=${e({"preview":this._inCardPicker})}
        .hass=${this.hass}
        .stateOverride=${(_d=(_c=(_b=this._templateResults)===null||_b===void 0?void 0:_b.tertiary)===null||_c===void 0?void 0:_c.result)!==null&&_d!==void 0?_d:tertiary}
        .verticalOffset=${ -19}
        .stateMargin=${this._stateMargin}
        small
      ></modern-circular-gauge-state>
      `;}const bigState=typeof((_e=this._config)===null||_e===void 0?void 0:_e.secondary)=="object"?((_g=(_f=this._config)===null||_f===void 0?void 0:_f.secondary)===null||_g===void 0?void 0:_g.state_size)=="big":false;if(!((_h=tertiary.show_state)!==null&&_h!==void 0?_h:true)||bigState){return x``;}const stateObj=this.hass.states[tertiary.entity||""];const templatedState=(_k=(_j=this._templateResults)===null||_j===void 0?void 0:_j.tertiaryEntity)===null||_k===void 0?void 0:_k.result;if(!stateObj&&templatedState===undefined){return x``;}const attributes=(_l=stateObj===null||stateObj===void 0?void 0:stateObj.attributes)!==null&&_l!==void 0?_l:undefined;const unit=(_m=tertiary.unit)!==null&&_m!==void 0?_m:attributes===null||attributes===void 0?void 0:attributes.unit_of_measurement;const state=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);const stateOverride=(_q=(_p=(_o=this._templateResults)===null||_o===void 0?void 0:_o.tertiaryStateText)===null||_p===void 0?void 0:_p.result)!==null&&_q!==void 0?_q:isTemplate(String(tertiary.state_text))?"":tertiary.state_text||undefined;const segments=(_t=(_s=(_r=this._templateResults)===null||_r===void 0?void 0:_r.tertiarySegments)===null||_s===void 0?void 0:_s.result)!==null&&_t!==void 0?_t:tertiary.segments;const segmentsLabel=this._getSegmentLabel(state,segments);let adaptiveColor;if(tertiary.adaptive_state_color){if(tertiary.show_gauge=="outter"){adaptiveColor=computeSegments(state,(_w=(_v=(_u=this._templateResults)===null||_u===void 0?void 0:_u.segments)===null||_v===void 0?void 0:_v.result)!==null&&_w!==void 0?_w:(_x=this._config)===null||_x===void 0?void 0:_x.segments,(_y=this._config)===null||_y===void 0?void 0:_y.smooth_segments,this);}else {adaptiveColor=computeSegments(state,segments,(_z=this._config)===null||_z===void 0?void 0:_z.smooth_segments,this);}if(((_0=tertiary.gauge_foreground_style)===null||_0===void 0?void 0:_0.color)&&((_1=tertiary.gauge_foreground_style)===null||_1===void 0?void 0:_1.color)!="adaptive"){adaptiveColor=(_2=tertiary.gauge_foreground_style)===null||_2===void 0?void 0:_2.color;}}return x`
    <modern-circular-gauge-state
      @action=${this._handleTertiaryAction}
      .actionHandler=${actionHandler({hasHold:hasAction(tertiary.hold_action),hasDoubleClick:hasAction(tertiary.double_tap_action)})}
      class=${e({"preview":this._inCardPicker})}
      style=${o$1({"--state-text-color-override":adaptiveColor!==null&&adaptiveColor!==void 0?adaptiveColor:undefined,"--state-font-size-override":tertiary.state_font_size?`${tertiary.state_font_size}px`:undefined})}
      .hass=${this.hass}
      .stateObj=${stateObj}
      .stateOverride=${(_3=segmentsLabel||stateOverride)!==null&&_3!==void 0?_3:templatedState}
      .unit=${unit}
      .verticalOffset=${ -19}
      .stateMargin=${this._stateMargin}
      .showUnit=${(_4=tertiary.show_unit)!==null&&_4!==void 0?_4:true}
      .label=${tertiary.label}
      .labelFontSize=${tertiary.label_font_size}
      small
    ></modern-circular-gauge-state>
    `;}_getSegmentLabel(numberState,segments){if(segments){let sortedSegments=[...segments].sort((a,b)=>Number(a.from)-Number(b.from));for(let i=sortedSegments.length-1;i>=0;i--){let segment=sortedSegments[i];if(numberState>=Number(segment.from)||i===0){return segment.label||"";}}}return "";}async _tryConnect(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o;const templates={entity:(_a=this._config)===null||_a===void 0?void 0:_a.entity,name:(_b=this._config)===null||_b===void 0?void 0:_b.name,icon:(_c=this._config)===null||_c===void 0?void 0:_c.icon,min:(_d=this._config)===null||_d===void 0?void 0:_d.min,max:(_e=this._config)===null||_e===void 0?void 0:_e.max,segments:(_f=this._config)===null||_f===void 0?void 0:_f.segments,stateText:(_g=this._config)===null||_g===void 0?void 0:_g.state_text,secondary:(_h=this._config)===null||_h===void 0?void 0:_h.secondary,tertiary:(_j=this._config)===null||_j===void 0?void 0:_j.tertiary};Object.entries(templates).forEach(([key,value])=>{if(typeof value=="string"){this._tryConnectKey(key,value);}else if(key=="segments"){const segmentsStringified=JSON.stringify(value);this._tryConnectKey(key,segmentsStringified);}});if(typeof((_k=this._config)===null||_k===void 0?void 0:_k.secondary)!="string"){const secondary=(_l=this._config)===null||_l===void 0?void 0:_l.secondary;const secondaryTemplates={secondaryMin:secondary===null||secondary===void 0?void 0:secondary.min,secondaryMax:secondary===null||secondary===void 0?void 0:secondary.max,secondaryEntity:secondary===null||secondary===void 0?void 0:secondary.entity,secondaryStateText:secondary===null||secondary===void 0?void 0:secondary.state_text,secondarySegments:secondary===null||secondary===void 0?void 0:secondary.segments};Object.entries(secondaryTemplates).forEach(([key,value])=>{if(typeof value=="string"){this._tryConnectKey(key,value);}else if(key=="secondarySegments"){const segmentsStringified=JSON.stringify(value);this._tryConnectKey(key,segmentsStringified);}});}if(typeof((_m=this._config)===null||_m===void 0?void 0:_m.tertiary)!="string"){const tertiary=(_o=this._config)===null||_o===void 0?void 0:_o.tertiary;const tertiaryTemplates={tertiaryMin:tertiary===null||tertiary===void 0?void 0:tertiary.min,tertiaryMax:tertiary===null||tertiary===void 0?void 0:tertiary.max,tertiaryEntity:tertiary===null||tertiary===void 0?void 0:tertiary.entity,tertiaryStateText:tertiary===null||tertiary===void 0?void 0:tertiary.state_text,tertiarySegments:tertiary===null||tertiary===void 0?void 0:tertiary.segments};Object.entries(tertiaryTemplates).forEach(([key,value])=>{if(typeof value=="string"){this._tryConnectKey(key,value);}else if(key=="tertiarySegments"){const segmentsStringified=JSON.stringify(value);this._tryConnectKey(key,segmentsStringified);}});}}async _tryConnectKey(key,templateValue){var _a,_b,_c;if(((_a=this._unsubRenderTemplates)===null||_a===void 0?void 0:_a.get(key))!==undefined||!this.hass||!this._config||!isTemplate(templateValue)){return;}try{const sub=subscribeRenderTemplate(this.hass.connection,result=>{if("error"in result){return;}this._templateResults=Object.assign(Object.assign({},this._templateResults),{[key]:result});},{template:templateValue||"",variables:{config:this._config,user:this.hass.user.name},strict:true});(_b=this._unsubRenderTemplates)===null||_b===void 0?void 0:_b.set(key,sub);await sub;}catch(e){const result={result:templateValue||"",listeners:{all:false,domains:[],entities:[],time:false}};this._templateResults=Object.assign(Object.assign({},this._templateResults),{[key]:result});(_c=this._unsubRenderTemplates)===null||_c===void 0?void 0:_c.delete(key);}}async _tryDisconnect(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o;const templates={entity:(_a=this._config)===null||_a===void 0?void 0:_a.entity,name:(_b=this._config)===null||_b===void 0?void 0:_b.name,icon:(_c=this._config)===null||_c===void 0?void 0:_c.icon,min:(_d=this._config)===null||_d===void 0?void 0:_d.min,max:(_e=this._config)===null||_e===void 0?void 0:_e.max,segments:(_f=this._config)===null||_f===void 0?void 0:_f.segments,stateText:(_g=this._config)===null||_g===void 0?void 0:_g.state_text,secondary:(_h=this._config)===null||_h===void 0?void 0:_h.secondary,tertiary:(_j=this._config)===null||_j===void 0?void 0:_j.tertiary};Object.entries(templates).forEach(([key,_])=>{this._tryDisconnectKey(key);});if(typeof((_k=this._config)===null||_k===void 0?void 0:_k.secondary)!="string"){const secondary=(_l=this._config)===null||_l===void 0?void 0:_l.secondary;const secondaryTemplates={secondaryMin:secondary===null||secondary===void 0?void 0:secondary.min,secondaryMax:secondary===null||secondary===void 0?void 0:secondary.max,secondaryEntity:secondary===null||secondary===void 0?void 0:secondary.entity,secondaryStateText:secondary===null||secondary===void 0?void 0:secondary.state_text,secondarySegments:secondary===null||secondary===void 0?void 0:secondary.segments};Object.entries(secondaryTemplates).forEach(([key,_])=>{this._tryDisconnectKey(key);});}if(typeof((_m=this._config)===null||_m===void 0?void 0:_m.tertiary)!="string"){const tertiary=(_o=this._config)===null||_o===void 0?void 0:_o.tertiary;const tertiaryTemplates={tertiaryMin:tertiary===null||tertiary===void 0?void 0:tertiary.min,tertiaryMax:tertiary===null||tertiary===void 0?void 0:tertiary.max,tertiaryEntity:tertiary===null||tertiary===void 0?void 0:tertiary.entity,tertiaryStateText:tertiary===null||tertiary===void 0?void 0:tertiary.state_text,tertiarySegments:tertiary===null||tertiary===void 0?void 0:tertiary.segments};Object.entries(tertiaryTemplates).forEach(([key,_])=>{this._tryDisconnectKey(key);});}}async _tryDisconnectKey(key){var _a,_b;const unsubRenderTemplate=(_a=this._unsubRenderTemplates)===null||_a===void 0?void 0:_a.get(key);if(!unsubRenderTemplate){return;}try{const unsub=await unsubRenderTemplate;unsub();(_b=this._unsubRenderTemplates)===null||_b===void 0?void 0:_b.delete(key);}catch(e){if(e.code==="not_found"||e.code==="template_error");else {throw e;}}}_handleAction(ev){var _a;ev.stopPropagation();const targetEntity=(_a=this._config)===null||_a===void 0?void 0:_a.entity;const config=Object.assign(Object.assign({},this._config),{entity:isTemplate(targetEntity!==null&&targetEntity!==void 0?targetEntity:"")?"":targetEntity});handleAction(this,this.hass,config,ev.detail.action);}_handleSecondaryAction(ev){var _a,_b,_c,_d,_e;ev.stopPropagation();if(typeof((_a=this._config)===null||_a===void 0?void 0:_a.secondary)!="string"){const entity=typeof((_b=this._config)===null||_b===void 0?void 0:_b.secondary)!="string"?(_d=(_c=this._config)===null||_c===void 0?void 0:_c.secondary)===null||_d===void 0?void 0:_d.entity:"";const config=Object.assign(Object.assign({},(_e=this._config)===null||_e===void 0?void 0:_e.secondary),{entity:isTemplate(entity!==null&&entity!==void 0?entity:"")?"":entity});handleAction(this,this.hass,config,ev.detail.action);}}_handleTertiaryAction(ev){var _a,_b,_c,_d,_e;ev.stopPropagation();if(typeof((_a=this._config)===null||_a===void 0?void 0:_a.tertiary)!="string"){const entity=typeof((_b=this._config)===null||_b===void 0?void 0:_b.tertiary)!="string"?(_d=(_c=this._config)===null||_c===void 0?void 0:_c.tertiary)===null||_d===void 0?void 0:_d.entity:"";const config=Object.assign(Object.assign({},(_e=this._config)===null||_e===void 0?void 0:_e.tertiary),{entity:isTemplate(entity!==null&&entity!==void 0?entity:"")?"":entity});handleAction(this,this.hass,config,ev.detail.action);}}getGridOptions(){return {columns:6,rows:4,min_rows:3,min_columns:4};}getLayoutOptions(){return {grid_columns:2,grid_rows:3,grid_min_rows:3,grid_min_columns:2};}getCardSize(){return 4;}static get styles(){return i$5`
    :host {
      --gauge-primary-color: var(--light-blue-color);
      --gauge-secondary-color: var(--orange-color);
      --gauge-tertiary-color: var(--light-green-color);

      --gauge-color: var(--gauge-primary-color);
      --gauge-stroke-width: 6px;
      --inner-gauge-stroke-width: 4px;
      --gauge-header-font-size: 14px;
    }

    ha-card {
      width: 100%;
      height: 100%;
      display: flex;
      padding: 10px;
      flex-direction: column-reverse;
      align-items: center;
    }

    ha-card.action {
      cursor: pointer
    }

    .flex-column-reverse {
      flex-direction: column;
    }
    
    .header {
      position: absolute;
      width: 100%;
      display: flex;
      flex-direction: column;
      text-align: center;
      padding: 0 10px;
      box-sizing: border-box;
    }

    .flex-column-reverse .header {
      position: relative;
    }
    
    .gauge-state {
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
      z-index: 2;
    }

    modern-circular-gauge-state {
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
    }

    .container {
      position: relative;
      container-type: inline-size;
      container-name: container;
      width: 100%;
      height: 100%;
    }

    .flex-column-reverse .container {
      margin-bottom: 0px;
    }

    .secondary, .tertiary-state {
      font-size: 10px;
      fill: var(--secondary-text-color);
      --gauge-color: var(--gauge-secondary-color);
    }

    .tertiary-state {
      --gauge-color: var(--gauge-tertiary-color);
    }

    .state-label {
      font-size: 0.49em;
      fill: var(--secondary-text-color);
    }

    .value, .secondary.dual-state {
      font-size: 21px;
      fill: var(--primary-text-color);
      dominant-baseline: middle;
    }

    .secondary.dual-state {
      fill: var(--secondary-text-color);
    }

    .secondary.dual-state .unit {
      opacity: 1;
    }

    modern-circular-gauge-icon {
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
      color: var(--primary-color);
    }

    .warning-icon {
      color: var(--state-unavailable-color);
    }

    .adaptive {
      color: var(--gauge-color);
    }

    .value.adaptive, .secondary.adaptive, .tertiary-state.adaptive {
      fill: var(--gauge-color);
    }

    .name {
      width: 100%;
      font-size: var(--gauge-header-font-size);
      margin: 0;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;

      line-height: 20px;
      letter-spacing: .1px;
      color: var(--primary-text-color);
    }

    .unit {
      font-size: .33em;
      opacity: 0.6;
    }

    .gauge-container {
      height: 100%;
      width: 100%;
      display: block;
    }

    modern-circular-gauge-element.secondary, modern-circular-gauge-element.tertiary {
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
    }

    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    g {
      fill: none;
    }
    .arc {
      fill: none;
      stroke-linecap: round;
      stroke-width: var(--gauge-stroke-width);
    }

    .arc.clear {
      stroke: var(--primary-background-color);
    }

    .arc.current {
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    .segment {
      fill: none;
      stroke-width: var(--gauge-stroke-width);
      filter: brightness(100%);
    }

    .segments {
      opacity: 0.35;
    }

    .needle {
      fill: none;
      stroke-linecap: round;
      stroke-width: var(--gauge-stroke-width);
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    .needle-border {
      fill: none;
      stroke-linecap: round;
      stroke-width: calc(var(--gauge-stroke-width) + 4px);
      stroke: var(--card-background-color);
      transition: all 1s ease 0s, stroke 0.3s ease-out;
    }

    .inner {
      --gauge-color: var(--gauge-secondary-color);
      --gauge-stroke-width: var(--inner-gauge-stroke-width);
    }

    .tertiary {
      --gauge-color: var(--gauge-tertiary-color);
    }

    .dual-gauge modern-circular-gauge-element {
      --gauge-stroke-width: 4px;
    }

    .dot {
      fill: none;
      stroke-linecap: round;
      stroke-width: calc(var(--gauge-stroke-width) / 2);
      stroke: var(--primary-text-color);
      transition: all 1s ease 0s;
    }

    .dot.border {
      stroke: var(--gauge-color);
      stroke-width: var(--gauge-stroke-width);
    }
    `;}};__decorate([n$1({attribute:false})],ModernCircularGauge.prototype,"hass",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_config",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_hasSecondary",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_templateResults",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_unsubRenderTemplates",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_stateMargin",void 0);__decorate([r$1()],ModernCircularGauge.prototype,"_inCardPicker",void 0);ModernCircularGauge=__decorate([t$1("modern-circular-gauge")],ModernCircularGauge);

function registerCustomBadge(params){const windowWithCards=window;windowWithCards.customBadges=windowWithCards.customBadges||[];windowWithCards.customBadges.push(Object.assign(Object.assign({},params),{preview:true,documentationURL:`https://github.com/selvalt7/modern-circular-gauge`}));}

// Material Design Icons v7.4.47
var mdiAlertCircle = "M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z";
var mdiClose = "M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z";
var mdiCodeBraces = "M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z";
var mdiFlipToBack = "M15,17H17V15H15M15,5H17V3H15M5,7H3V19A2,2 0 0,0 5,21H17V19H5M19,17A2,2 0 0,0 21,15H19M19,9H21V7H19M19,13H21V11H19M9,17V15H7A2,2 0 0,0 9,17M13,3H11V5H13M19,3V5H21C21,3.89 20.1,3 19,3M13,15H11V17H13M9,3C7.89,3 7,3.89 7,5H9M9,11H7V13H9M9,7H7V9H9V7Z";
var mdiFlipToFront = "M7,21H9V19H7M11,21H13V19H11M19,15H9V5H19M19,3H9C7.89,3 7,3.89 7,5V15A2,2 0 0,0 9,17H14L18,17H19A2,2 0 0,0 21,15V5C21,3.89 20.1,3 19,3M15,21H17V19H15M3,9H5V7H3M5,21V19H3A2,2 0 0,0 5,21M3,17H5V15H3M3,13H5V11H3V13Z";
var mdiGauge = "M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12C20,14.4 19,16.5 17.3,18C15.9,16.7 14,16 12,16C10,16 8.2,16.7 6.7,18C5,16.5 4,14.4 4,12A8,8 0 0,1 12,4M14,5.89C13.62,5.9 13.26,6.15 13.1,6.54L11.81,9.77L11.71,10C11,10.13 10.41,10.6 10.14,11.26C9.73,12.29 10.23,13.45 11.26,13.86C12.29,14.27 13.45,13.77 13.86,12.74C14.12,12.08 14,11.32 13.57,10.76L13.67,10.5L14.96,7.29L14.97,7.26C15.17,6.75 14.92,6.17 14.41,5.96C14.28,5.91 14.15,5.89 14,5.89M10,6A1,1 0 0,0 9,7A1,1 0 0,0 10,8A1,1 0 0,0 11,7A1,1 0 0,0 10,6M7,9A1,1 0 0,0 6,10A1,1 0 0,0 7,11A1,1 0 0,0 8,10A1,1 0 0,0 7,9M17,9A1,1 0 0,0 16,10A1,1 0 0,0 17,11A1,1 0 0,0 18,10A1,1 0 0,0 17,9Z";
var mdiListBoxOutline = "M11 15H17V17H11V15M9 7H7V9H9V7M11 13H17V11H11V13M11 9H17V7H11V9M9 11H7V13H9V11M21 5V19C21 20.1 20.1 21 19 21H5C3.9 21 3 20.1 3 19V5C3 3.9 3.9 3 5 3H19C20.1 3 21 3.9 21 5M19 5H5V19H19V5M9 15H7V17H9V15Z";
var mdiNumeric2BoxOutline = "M15,15H11V13H13A2,2 0 0,0 15,11V9C15,7.89 14.1,7 13,7H9V9H13V11H11A2,2 0 0,0 9,13V17H15M19,19H5V5H19M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3Z";
var mdiNumeric3BoxOutline = "M15,15V13.5A1.5,1.5 0 0,0 13.5,12A1.5,1.5 0 0,0 15,10.5V9C15,7.89 14.1,7 13,7H9V9H13V11H11V13H13V15H9V17H13A2,2 0 0,0 15,15M19,19H5V5H19M19,3H5A2,2 0 0,0 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5A2,2 0 0,0 19,3Z";
var mdiPalette = "M17.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,9A1.5,1.5 0 0,1 19,10.5A1.5,1.5 0 0,1 17.5,12M14.5,8A1.5,1.5 0 0,1 13,6.5A1.5,1.5 0 0,1 14.5,5A1.5,1.5 0 0,1 16,6.5A1.5,1.5 0 0,1 14.5,8M9.5,8A1.5,1.5 0 0,1 8,6.5A1.5,1.5 0 0,1 9.5,5A1.5,1.5 0 0,1 11,6.5A1.5,1.5 0 0,1 9.5,8M6.5,12A1.5,1.5 0 0,1 5,10.5A1.5,1.5 0 0,1 6.5,9A1.5,1.5 0 0,1 8,10.5A1.5,1.5 0 0,1 6.5,12M12,3A9,9 0 0,0 3,12A9,9 0 0,0 12,21A1.5,1.5 0 0,0 13.5,19.5C13.5,19.11 13.35,18.76 13.11,18.5C12.88,18.23 12.73,17.88 12.73,17.5A1.5,1.5 0 0,1 14.23,16H16A5,5 0 0,0 21,11C21,6.58 16.97,3 12,3Z";
var mdiPlus = "M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z";
var mdiSegment = "M21,8H3V6H21M9,13H21V11H9M9,18H21V16H9";

const MAX_ANGLE=270;const ROTATE_ANGLE=360-MAX_ANGLE/2-90;const RADIUS=42;registerCustomBadge({type:"modern-circular-gauge-badge",name:"Modern Circular Gauge Badge",description:"Modern circular gauge badge"});const path=svgArc({x:0,y:0,start:0,end:MAX_ANGLE,r:RADIUS});let ModernCircularGaugeBadge=class ModernCircularGaugeBadge extends i$2{constructor(){super(...arguments);this._templateResults={};this._unsubRenderTemplates=new Map();}static async getStubConfig(hass){const entities=Object.keys(hass.states);const numbers=entities.filter(e=>NUMBER_ENTITY_DOMAINS.includes(e.split(".")[0]));return {type:"custom:modern-circular-gauge-badge",entity:numbers[0]};}static async getConfigElement(){await Promise.resolve().then(function () { return gaugeBadgeEditor; });return document.createElement("modern-circular-gauge-badge-editor");}setConfig(config){if(!config.entity){throw new Error("Entity must be specified");}this._config=Object.assign({min:DEFAULT_MIN,max:DEFAULT_MAX,show_state:true},config);}connectedCallback(){super.connectedCallback();this._tryConnect();}disconnectedCallback(){super.disconnectedCallback();this._tryDisconnect();}updated(changedProps){super.updated(changedProps);if(!this._config||!this.hass){return;}this._tryConnect();}async _tryConnect(){var _a,_b,_c,_d,_e,_f,_g;const templates={entity:(_a=this._config)===null||_a===void 0?void 0:_a.entity,name:(_b=this._config)===null||_b===void 0?void 0:_b.name,icon:(_c=this._config)===null||_c===void 0?void 0:_c.icon,min:(_d=this._config)===null||_d===void 0?void 0:_d.min,max:(_e=this._config)===null||_e===void 0?void 0:_e.max,segments:(_f=this._config)===null||_f===void 0?void 0:_f.segments,stateText:(_g=this._config)===null||_g===void 0?void 0:_g.state_text};Object.entries(templates).forEach(([key,value])=>{if(typeof value=="string"){this._tryConnectKey(key,value);}else if(key=="segments"){const segmentsStringified=JSON.stringify(value);this._tryConnectKey(key,segmentsStringified);}});}async _tryConnectKey(key,templateValue){var _a,_b,_c;if(((_a=this._unsubRenderTemplates)===null||_a===void 0?void 0:_a.get(key))!==undefined||!this.hass||!this._config||!isTemplate(templateValue)){return;}try{const sub=subscribeRenderTemplate(this.hass.connection,result=>{if("error"in result){return;}this._templateResults=Object.assign(Object.assign({},this._templateResults),{[key]:result});},{template:templateValue||"",variables:{config:this._config,user:this.hass.user.name},strict:true});(_b=this._unsubRenderTemplates)===null||_b===void 0?void 0:_b.set(key,sub);await sub;}catch(e){const result={result:templateValue||"",listeners:{all:false,domains:[],entities:[],time:false}};this._templateResults=Object.assign(Object.assign({},this._templateResults),{[key]:result});(_c=this._unsubRenderTemplates)===null||_c===void 0?void 0:_c.delete(key);}}async _tryDisconnect(){var _a,_b,_c,_d,_e,_f,_g;const templates={entity:(_a=this._config)===null||_a===void 0?void 0:_a.entity,name:(_b=this._config)===null||_b===void 0?void 0:_b.name,icon:(_c=this._config)===null||_c===void 0?void 0:_c.icon,min:(_d=this._config)===null||_d===void 0?void 0:_d.min,max:(_e=this._config)===null||_e===void 0?void 0:_e.max,segments:(_f=this._config)===null||_f===void 0?void 0:_f.segments,stateText:(_g=this._config)===null||_g===void 0?void 0:_g.state_text};Object.entries(templates).forEach(([key,_])=>{this._tryDisconnectKey(key);});}async _tryDisconnectKey(key){var _a,_b;const unsubRenderTemplate=(_a=this._unsubRenderTemplates)===null||_a===void 0?void 0:_a.get(key);if(!unsubRenderTemplate){return;}try{const unsub=await unsubRenderTemplate;unsub();(_b=this._unsubRenderTemplates)===null||_b===void 0?void 0:_b.delete(key);}catch(e){if(e.code==="not_found"||e.code==="template_error");else {throw e;}}}get hasAction(){var _a,_b,_c,_d;return !((_a=this._config)===null||_a===void 0?void 0:_a.tap_action)||hasAction((_b=this._config)===null||_b===void 0?void 0:_b.tap_action)||hasAction((_c=this._config)===null||_c===void 0?void 0:_c.hold_action)||hasAction((_d=this._config)===null||_d===void 0?void 0:_d.double_tap_action);}render(){var _a,_b,_c,_d,_e,_f,_g,_h,_j,_k,_l,_m,_o,_p,_q,_r,_s,_t,_u,_v,_w,_x,_y,_z,_0,_1,_2,_3,_4,_5,_6,_7,_8,_9,_10,_11,_12,_13,_14,_15,_16,_17,_18,_19,_20,_21;if(!this.hass||!this._config){return x``;}const stateObj=this.hass.states[this._config.entity];const templatedState=(_b=(_a=this._templateResults)===null||_a===void 0?void 0:_a.entity)===null||_b===void 0?void 0:_b.result;if(!stateObj&&templatedState===undefined){if(isTemplate(this._config.entity)){return this._renderWarning();}else {return this._renderWarning(this._config.entity,this.hass.localize("ui.badge.entity.not_found"),undefined,"error",mdiAlertCircle);}}const numberState=Number(templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state);const icon=(_e=(_d=(_c=this._templateResults)===null||_c===void 0?void 0:_c.icon)===null||_d===void 0?void 0:_d.result)!==null&&_e!==void 0?_e:this._config.icon;if((stateObj===null||stateObj===void 0?void 0:stateObj.state)==="unavailable"){return this._renderWarning((_k=(_j=(_h=(_g=(_f=this._templateResults)===null||_f===void 0?void 0:_f.name)===null||_g===void 0?void 0:_g.result)!==null&&_h!==void 0?_h:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_j!==void 0?_j:stateObj.attributes.friendly_name)!==null&&_k!==void 0?_k:'',this.hass.localize("state.default.unavailable"),stateObj,"warning",icon);}if(isNaN(numberState)){return this._renderWarning((_q=(_p=(_o=(_m=(_l=this._templateResults)===null||_l===void 0?void 0:_l.name)===null||_m===void 0?void 0:_m.result)!==null&&_o!==void 0?_o:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_p!==void 0?_p:stateObj.attributes.friendly_name)!==null&&_q!==void 0?_q:'',"NaN",stateObj,"warning",icon);}const min=(_u=Number((_t=(_s=(_r=this._templateResults)===null||_r===void 0?void 0:_r.min)===null||_s===void 0?void 0:_s.result)!==null&&_t!==void 0?_t:this._config.min))!==null&&_u!==void 0?_u:DEFAULT_MIN;const max=(_y=Number((_x=(_w=(_v=this._templateResults)===null||_v===void 0?void 0:_v.max)===null||_w===void 0?void 0:_w.result)!==null&&_x!==void 0?_x:this._config.max))!==null&&_y!==void 0?_y:DEFAULT_MAX;const attributes=(_z=stateObj===null||stateObj===void 0?void 0:stateObj.attributes)!==null&&_z!==void 0?_z:undefined;const current=this._config.needle?undefined:currentDashArc(numberState,min,max,RADIUS,this._config.start_from_zero);const state=templatedState!==null&&templatedState!==void 0?templatedState:stateObj.state;const stateOverride=(_2=(_1=(_0=this._templateResults)===null||_0===void 0?void 0:_0.stateText)===null||_1===void 0?void 0:_1.result)!==null&&_2!==void 0?_2:isTemplate(String(this._config.state_text))?"":this._config.state_text||undefined;const unit=((_3=this._config.show_unit)!==null&&_3!==void 0?_3:true)?((_4=this._config.unit)!==null&&_4!==void 0?_4:stateObj===null||stateObj===void 0?void 0:stateObj.attributes.unit_of_measurement)||"":"";const entityState=(_5=stateOverride!==null&&stateOverride!==void 0?stateOverride:formatNumber(state,this.hass.locale,getNumberFormatOptions({state,attributes},this.hass.entities[stateObj===null||stateObj===void 0?void 0:stateObj.entity_id])))!==null&&_5!==void 0?_5:templatedState;const showIcon=(_6=this._config.show_icon)!==null&&_6!==void 0?_6:true;const name=(_11=(_10=(_9=(_8=(_7=this._templateResults)===null||_7===void 0?void 0:_7.name)===null||_8===void 0?void 0:_8.result)!==null&&_9!==void 0?_9:isTemplate(String(this._config.name))?"":this._config.name)!==null&&_10!==void 0?_10:stateObj===null||stateObj===void 0?void 0:stateObj.attributes.friendly_name)!==null&&_11!==void 0?_11:"";const label=this._config.show_name&&showIcon&&this._config.show_state?name:undefined;const content=showIcon&&this._config.show_state?`${entityState} ${unit}`:this._config.show_name?name:undefined;const segments=(_14=(_13=(_12=this._templateResults)===null||_12===void 0?void 0:_12.segments)===null||_13===void 0?void 0:_13.result)!==null&&_14!==void 0?_14:this._config.segments;const gaugeBackgroundStyle=this._config.gauge_background_style;const gaugeForegroundStyle=this._config.gauge_foreground_style;return x`
    <ha-badge
      .type=${this.hasAction?"button":"badge"}
      @action=${this._handleAction}
      .actionHandler=${actionHandler({hasHold:hasAction(this._config.hold_action),hasDoubleClick:hasAction(this._config.double_tap_action)})}
      .iconOnly=${content===undefined}
      style=${o$1({"--gauge-color":(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.color)&&(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.color)!="adaptive"?gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.color:computeSegments(numberState,segments,this._config.smooth_segments,this),"--gauge-stroke-width":(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width)?`${gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width}px`:undefined})}
      .label=${label}
    >
      <div class=${e({"container":true,"icon-only":content===undefined})} slot="icon">
        <svg class="gauge" viewBox="-50 -50 100 100">
          <g transform="rotate(${ROTATE_ANGLE})">
            <defs>
            ${this._config.needle?b`
              <mask id="needle-mask">
                ${renderPath("arc",path,undefined,o$1({"stroke":"white","stroke-width":(gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.width)?`${gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.width}px`:undefined}))}
                <circle cx="42" cy="0" r=${(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width)?(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width)-2:12} fill="black" transform="rotate(${getAngle(numberState,min,max)})"/>
              </mask>
              `:E}
              <mask id="gradient-path">
                ${renderPath("arc",path,undefined,o$1({"stroke":"white","stroke-width":(gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.width)?`${gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.width}px`:undefined}))}
              </mask>
              <mask id="gradient-current-path">
                ${current?renderPath("arc current",path,current,o$1({"stroke":"white","visibility":numberState<=min&&min>=0?"hidden":"visible"})):E}
              </mask>
            </defs>
            <g mask="url(#needle-mask)">
              <g class="background" style=${o$1({"opacity":(_15=this._config.gauge_background_style)===null||_15===void 0?void 0:_15.opacity,"--gauge-stroke-width":((_16=this._config.gauge_background_style)===null||_16===void 0?void 0:_16.width)?`${(_17=this._config.gauge_background_style)===null||_17===void 0?void 0:_17.width}px`:undefined})}>
                ${renderPath("arc clear",path,undefined,o$1({"stroke":(gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.color)&&(gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.color)!="adaptive"?gaugeBackgroundStyle===null||gaugeBackgroundStyle===void 0?void 0:gaugeBackgroundStyle.color:undefined}))}
                ${this._config.segments&&(this._config.needle||((_18=this._config.gauge_background_style)===null||_18===void 0?void 0:_18.color)=="adaptive")?b`
                <g class="segments" mask=${o(this._config.smooth_segments?"url(#gradient-path)":undefined)}>
                  ${renderColorSegments(segments,min,max,RADIUS,(_19=this._config)===null||_19===void 0?void 0:_19.smooth_segments)}
                </g>`:E}
              </g>
            </g>
          ${this._config.needle?b`
            <circle class="needle" cx="42" cy="0" r=${(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width)?(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.width)/2:7} transform="rotate(${getAngle(numberState,min,max)})"/>
          `:E}
          ${current?(gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.color)=="adaptive"?b`
            <g class="foreground-segments" mask="url(#gradient-current-path)" style=${o$1({"opacity":gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.opacity})}>
              ${renderColorSegments(segments,min,max,RADIUS,(_20=this._config)===null||_20===void 0?void 0:_20.smooth_segments)}
            </g>
            `:renderPath("arc current",path,current,o$1({"visibility":numberState<=min&&min>=0?"hidden":"visible","opacity":gaugeForegroundStyle===null||gaugeForegroundStyle===void 0?void 0:gaugeForegroundStyle.opacity})):E}
          </g>
        </svg>
        ${showIcon?x`
          <ha-state-icon
            .hass=${this.hass}
            .stateObj=${stateObj}
            .icon=${icon}
          ></ha-state-icon>`:E}
        ${this._config.show_state&&!showIcon?x`
          <svg class="state" viewBox="-50 -50 100 100">
            <text x="0" y="0" class="value" style=${o$1({"font-size":this._calcStateSize(entityState)})}>
              ${entityState}
              ${((_21=this._config.show_unit)!==null&&_21!==void 0?_21:true)?b`
              <tspan class="unit" dx="-4" dy="-6">${unit}</tspan>
              `:E}
            </text>
          </svg>
          `:E}
      </div>
      ${content}
    </ha-badge>
    `;}_renderWarning(label,content,stateObj,badgeClass,icon){var _a,_b,_c;return x`
    <ha-badge
      .type=${((_a=this.hasAction)!==null&&_a!==void 0?_a:stateObj!=undefined)?"button":"badge"}
      @action=${o(stateObj?this._handleAction:undefined)}
      .actionHandler=${actionHandler({hasHold:hasAction((_b=this._config)===null||_b===void 0?void 0:_b.hold_action),hasDoubleClick:hasAction((_c=this._config)===null||_c===void 0?void 0:_c.double_tap_action)})}
      class="${o(badgeClass)}"
      .label=${label} 
      >
      <div class=${e({"container":true,"icon-only":content===undefined})} slot="icon">
        <svg class="gauge" viewBox="-50 -50 100 100">
          <g transform="rotate(${ROTATE_ANGLE})">
            ${renderPath("arc clear",path)}
          </g>
        </svg>
        ${stateObj?x`
        <ha-state-icon
          slot="icon"
          .hass=${this.hass}
          .stateObj=${stateObj}
          .icon=${icon}
        ></ha-state-icon>
        `:x`
        <ha-svg-icon
          slot="icon"
          .path=${icon}
        ></ha-svg-icon>
        `}
      </div>
      ${content}
    </ha-badge>
    `;}_calcStateSize(state){const initialSize=25;if(state.length>=4){return `${initialSize-(state.length-3)}px`;}return `${initialSize}px`;}_handleAction(ev){var _a,_b,_c;const config=Object.assign(Object.assign({},this._config),{entity:isTemplate((_b=(_a=this._config)===null||_a===void 0?void 0:_a.entity)!==null&&_b!==void 0?_b:"")?"":(_c=this._config)===null||_c===void 0?void 0:_c.entity});handleAction(this,this.hass,config,ev.detail.action);}static get styles(){return i$5`
    :host {
      --gauge-color: var(--primary-color);
      --gauge-stroke-width: 14px;
    }

    .badge::slotted([slot=icon]) {
      margin-left: 0;
      margin-right: 0;
      margin-inline-start: 0;
      margin-inline-end: 0;
    }

    .state {
      position: absolute;
      top: 0;
      bottom: 0;
      left: 0;
      right: 0;
      text-anchor: middle;
    }

    .value {
      font-size: 21px;
      fill: var(--primary-text-color);
      dominant-baseline: middle;
    }

    .unit {
      font-size: .43em;
      opacity: 0.6;
    }

    .container {
      display: flex;
      justify-content: center;
      align-items: center;
      position: relative;
      container-type: normal;
      container-name: container;
      width: calc(var(--ha-badge-size, 36px) - 2px);
      height: calc(var(--ha-badge-size, 36px) - 2px);
      margin-left: -12px;
      margin-inline-start: -12px;
      pointer-events: none;
    }

    .container.icon-only {
      margin-left: 0;
      margin-inline-start: 0;
    }

    .gauge {
      position: absolute;
    }

    .segment {
      fill: none;
      stroke-width: var(--gauge-stroke-width);
      filter: brightness(100%);
    }

    .segments {
      opacity: 0.45;
    }

    ha-badge {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      --badge-color: var(--gauge-color);
    }

    ha-badge.error {
      --badge-color: var(--red-color);
    }

    ha-badge.warning {
      --badge-color: var(--state-unavailable-color);
    }

    svg {
      width: 100%;
      height: 100%;
      display: block;
    }
    g {
      fill: none;
    }
    .arc {
      fill: none;
      stroke-linecap: round;
      stroke-width: var(--gauge-stroke-width);
    }

    .arc.clear {
      stroke: var(--primary-background-color);
    }

    .arc.current {
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    .needle {
      fill: var(--gauge-color);
      stroke: var(--gauge-color);
      transition: all 1s ease 0s;
    }

    circle {
      transition: all 1s ease 0s;
    }
    `;}};__decorate([n$1({attribute:false})],ModernCircularGaugeBadge.prototype,"hass",void 0);__decorate([r$1()],ModernCircularGaugeBadge.prototype,"_config",void 0);__decorate([r$1()],ModernCircularGaugeBadge.prototype,"_templateResults",void 0);__decorate([r$1()],ModernCircularGaugeBadge.prototype,"_unsubRenderTemplates",void 0);ModernCircularGaugeBadge=__decorate([t$1("modern-circular-gauge-badge")],ModernCircularGaugeBadge);

var version = "0.11.2";

console.log(`%cModern Circular Gauge%cv${version}`,"background-color: #57BB30; color: #2C412D; padding: 4px 6px; font-weight: bold","background-color: gray; padding: 4px 6px; font-weight: bold");

const getSecondaryGaugeSchema=showGaugeOptions=>[{name:"show_gauge",selector:{select:{options:[{value:"none",label:"None"},{value:"inner",label:"Inner gauge"},{value:"outer",label:"Outer gauge"}],mode:"dropdown",translation_key:"show_gauge_options"}}},{name:"",type:"grid",disabled:!showGaugeOptions,schema:[{name:"min",type:"mcg-template",default:DEFAULT_MIN,schema:{number:{step:0.1}}},{name:"max",type:"mcg-template",default:DEFAULT_MAX,schema:{number:{step:0.1}}}]}];const getSegmentsSchema=()=>[{name:"segments",type:"mcg-list",iconPath:mdiSegment,schema:[{name:"",type:"grid",column_min_width:"100px",schema:[{name:"from",type:"mcg-template",required:true,schema:{number:{step:0.1}}},{name:"color",type:"mcg-template",required:true,schema:{color_rgb:{}}}]}]}];const getGaugeStyleSchema=(gaugeDefaultWidth=6)=>[{name:"",type:"grid",schema:[{name:"width",default:gaugeDefaultWidth,selector:{number:{step:"any",min:0}}},{name:"color",helper:"gauge_color",selector:{text:{}}},{name:"opacity",default:1,selector:{number:{step:"any",min:0,max:1}}}]}];const getEntityStyleSchema=(showGaugeOptions,gaugeDefaultRadius=RADIUS$1,labelHelper="label")=>[{name:"label",helper:labelHelper,selector:{text:{}}},{name:"",type:"grid",schema:[{name:"needle",disabled:!showGaugeOptions,selector:{boolean:{}}},{name:"start_from_zero",helper:"start_from_zero",disabled:!showGaugeOptions,selector:{boolean:{}}},{name:"show_state",default:true,selector:{boolean:{}}},{name:"show_unit",default:true,selector:{boolean:{}}},{name:"adaptive_state_color",default:false,selector:{boolean:{}}}]},{name:"state_text",helper:"state_text",selector:{template:{}}},{name:"gauge_radius",default:gaugeDefaultRadius,disabled:!showGaugeOptions,selector:{number:{step:1}}},{name:"gauge_foreground_style",type:"expandable",disabled:!showGaugeOptions,iconPath:mdiFlipToFront,schema:getGaugeStyleSchema(gaugeDefaultRadius==RADIUS$1?6:4)},{name:"gauge_background_style",type:"expandable",disabled:!showGaugeOptions,iconPath:mdiFlipToBack,schema:getGaugeStyleSchema(gaugeDefaultRadius==RADIUS$1?6:4)}];function getSecondarySchema(showGaugeOptions){return {name:"secondary",type:"expandable",iconPath:mdiNumeric2BoxOutline,schema:[{name:"entity",type:"mcg-template",schema:{entity:{domain:NUMBER_ENTITY_DOMAINS}}},{name:"",type:"grid",schema:[{name:"unit",selector:{text:{}}},{name:"state_size",selector:{select:{options:[{value:"small",label:"Small"},{value:"big",label:"Big"}],mode:"dropdown",translation_key:"state_size_options"}}}]},...getSecondaryGaugeSchema(showGaugeOptions),{name:"secondary_entity_style",type:"expandable",flatten:true,iconPath:mdiGauge,schema:getEntityStyleSchema(showGaugeOptions,INNER_RADIUS)},...getSegmentsSchema(),{name:"tap_action",selector:{ui_action:{}}}]};}function getTertiarySchema(showGaugeOptions){return {name:"tertiary",type:"expandable",iconPath:mdiNumeric3BoxOutline,schema:[{name:"entity",type:"mcg-template",schema:{entity:{domain:NUMBER_ENTITY_DOMAINS}}},{name:"unit",selector:{text:{}}},...getSecondaryGaugeSchema(showGaugeOptions),{name:"tertiary_entity_style",type:"expandable",flatten:true,iconPath:mdiGauge,schema:getEntityStyleSchema(showGaugeOptions,TERTIARY_RADIUS)},...getSegmentsSchema(),{name:"tap_action",selector:{ui_action:{}}}]};}

var safeIsNaN = Number.isNaN ||
    function ponyfill(value) {
        return typeof value === 'number' && value !== value;
    };
function isEqual(first, second) {
    if (first === second) {
        return true;
    }
    if (safeIsNaN(first) && safeIsNaN(second)) {
        return true;
    }
    return false;
}
function areInputsEqual(newInputs, lastInputs) {
    if (newInputs.length !== lastInputs.length) {
        return false;
    }
    for (var i = 0; i < newInputs.length; i++) {
        if (!isEqual(newInputs[i], lastInputs[i])) {
            return false;
        }
    }
    return true;
}

function memoizeOne(resultFn, isEqual) {
    if (isEqual === void 0) { isEqual = areInputsEqual; }
    var cache = null;
    function memoized() {
        var newArgs = [];
        for (var _i = 0; _i < arguments.length; _i++) {
            newArgs[_i] = arguments[_i];
        }
        if (cache && cache.lastThis === this && isEqual(newArgs, cache.lastArgs)) {
            return cache.lastResult;
        }
        var lastResult = resultFn.apply(this, newArgs);
        cache = {
            lastResult: lastResult,
            lastArgs: newArgs,
            lastThis: this,
        };
        return lastResult;
    }
    memoized.clear = function clear() {
        cache = null;
    };
    return memoized;
}

var editor$1 = {
	min: "Minimum",
	max: "Maximum",
	needle: "Display as needle gauge",
	secondary: "Secondary info",
	tertiary: "Tertiary info",
	state_size: "State size",
	show_gauge: "Gauge visibility",
	header_position: "Header position",
	show_header: "Show header",
	adaptive_icon_color: "Adaptive icon color",
	icon_entity: "Icon entity",
	adaptive_state_color: "Adaptive state color",
	show_unit: "Show unit",
	smooth_segments: "Smooth segments",
	segments: "Color segments",
	from: "From",
	color: "Color",
	label: "Label",
	switch_to_form: "Switch To Form",
	switch_to_template: "Switch To Template",
	start_from_zero: "Start from zero",
	gauge_radius: "Gauge radius",
	width: "Width",
	opacity: "Opacity",
	gauge_foreground_style: "Gauge foreground style",
	gauge_background_style: "Gauge background style",
	appearance: "Card appearance",
	badge_appearance: "Badge appearance",
	state_text: "State text",
	primary_entity_style: "Entity style",
	secondary_entity_style: "Entity style",
	tertiary_entity_style: "Entity style",
	helper: {
		start_from_zero: "Gauge starts from zero instead of min",
		primary_label: "Text displayed under the main state when secondary state size is set to big",
		label: "Text displayed under the state",
		gauge_color: "Accepts hex, rgb, CSS variables or \"adaptive\" for segmented style",
		icon_entity: "Select which entity to use for icon selection and coloring",
		state_text: "Overrides displayed state without overriding gauge data, accepts template"
	},
	header_position_options: {
		options: {
			top: "Top",
			bottom: "Bottom"
		}
	},
	icon_entity_options: {
		options: {
			primary: "Primary",
			secondary: "Secondary",
			tertiary: "Tertiary"
		}
	},
	show_gauge_options: {
		options: {
			none: "None",
			inner: "Inner gauge",
			outer: "Outer gauge"
		}
	},
	state_size_options: {
		options: {
			small: "Small",
			big: "Big"
		}
	}
};
var en = {
	editor: editor$1
};

var en$1 = /*#__PURE__*/Object.freeze({
    __proto__: null,
    default: en,
    editor: editor$1
});

var editor = {
	min: "Minimum",
	max: "Maksimum",
	needle: "Wyświetl jako wskaźnik igłowy",
	secondary: "Informacja drugorzędna",
	tertiary: "Informacja trzeciorzędna",
	state_size: "Rozmiar stanu",
	show_gauge: "Widoczność wskaźnika",
	header_position: "Pozycja nagłówka",
	show_header: "Pokaż nagłówek",
	adaptive_icon_color: "Adaptywny kolor ikony",
	icon_entity: "Encja ikony",
	adaptive_state_color: "Adaptywny kolor stanu",
	show_unit: "Pokaż jednostkę",
	smooth_segments: "Wygładzone segmenty",
	segments: "Segmenty kolorów",
	from: "Od",
	color: "Kolor",
	label: "Etykieta",
	switch_to_form: "Przełącz na Selektor",
	switch_to_template: "Przełącz na Template",
	start_from_zero: "Rozpocznij od zera",
	gauge_radius: "Promień wskaźnika",
	width: "Szerokość",
	opacity: "Nieprzezroczystość",
	gauge_foreground_style: "Styl wskaźnika",
	gauge_background_style: "Styl tła wskaźnika",
	appearance: "Wygląd karty",
	badge_appearance: "Wygląd odznaki",
	state_text: "Tekst stanu",
	primary_entity_style: "Styl encji",
	secondary_entity_style: "Styl encji",
	tertiary_entity_style: "Styl encji",
	helper: {
		start_from_zero: "Wskaźnik rozpoczyna się od zera zamiast od minimum",
		primary_label: "Tekst wyświetlony pod głównym stanem, gdy rozmiar stanu informacji drugorzędnej jest duży",
		label: "Tekst wyświetlony pod stanem",
		gauge_color: "Przyjmuje wartości hex, rgb, zmienne CSS lub \"adaptive\" dla stylu segmentów kolorów",
		icon_entity: "Wybierz encję, której chcesz użyć do wyboru ikon i ich kolorowania",
		state_text: "Nadpisuje wyświetlany stan bez nadpisywania danych wskaźnika, akceptuje template"
	},
	header_position_options: {
		options: {
			top: "Na górze",
			bottom: "Na dole"
		}
	},
	icon_entity_options: {
		options: {
			primary: "Pierwszorzędna",
			secondary: "Drugorzędna",
			tertiary: "Trzeciorzędna"
		}
	},
	show_gauge_options: {
		options: {
			none: "Brak",
			inner: "Wewnętrzny wskaźnik",
			outer: "Zewnętrzny wskaźnik"
		}
	},
	state_size_options: {
		options: {
			small: "Mały",
			big: "Duży"
		}
	}
};
var pl = {
	editor: editor
};

var pl$1 = /*#__PURE__*/Object.freeze({
    __proto__: null,
    default: pl,
    editor: editor
});

const languages={en: en$1,pl: pl$1};const DEFAULT_LANG="en";function getTranslatedString(key,lang=DEFAULT_LANG){try{return key.split('.').reduce((o,i)=>o[i],languages[lang]);}catch(_){return undefined;}}function localize(hass,key){const lang=hass.locale.language||DEFAULT_LANG;let translatedString=getTranslatedString(key,lang);if(!translatedString){translatedString=getTranslatedString(key,DEFAULT_LANG);}return translatedString!==null&&translatedString!==void 0?translatedString:key;}

let MCG_List=class MCG_List extends i$2{constructor(){super(...arguments);this.disabled=false;this._computeLabel=(schema,data,options)=>{if(!this.computeLabel)return this._computeLabel;return this.computeLabel(schema,data,Object.assign(Object.assign({},options),{path:[...((options===null||options===void 0?void 0:options.path)||[]),this.schema.name]}));};}render(){var _a,_b;return x`
    <ha-expansion-panel outlined .expanded=${Boolean(this.schema.expanded)}>
      <div
        slot="header"
        role="heading"
      >
        <ha-svg-icon .path=${this.schema.iconPath}></ha-svg-icon>
        ${localize(this.hass,`editor.${this.schema.name}`)}
      </div>
      <div class="content">
        ${this.data?this.data.map((row,index)=>x`
          <div class="entry">
            <ha-form
              .hass=${this.hass}
              .data=${row}
              .schema=${this.schema.schema}
              .index=${index}
              .disabled=${this.disabled}
              .computeLabel=${this._computeLabel}
              @value-changed=${this._valueChanged}
            ></ha-form>
            <ha-icon-button
              .label=${this.hass.localize("ui.common.remove")}
              .path=${mdiClose}
              .index=${index}
              @click=${this._removeRow}
            >
          </div>
        `):E}
        <ha-button .disabled=${this.disabled} @click=${this._addRow}>
          ${(_b=(_a=this.hass)===null||_a===void 0?void 0:_a.localize("ui.common.add"))!==null&&_b!==void 0?_b:"Add"}
          <ha-svg-icon slot="icon" .path=${mdiPlus}></ha-svg-icon>
        </ha-button>
      </div>
    </ha-expansion-panel>
    `;}_valueChanged(ev){ev.stopPropagation();const data=[...this.data];data[ev.target.index]=ev.detail.value;fireEvent(this,"value-changed",{value:data});}_addRow(){if(this.data===undefined){fireEvent(this,"value-changed",{value:[{}]});return;}const data=[...this.data,{}];fireEvent(this,"value-changed",{value:data});}_removeRow(ev){const data=[...this.data];data.splice(ev.target.index,1);fireEvent(this,"value-changed",{value:data});}static get styles(){return i$5`
      .content {
        display: flex;
        justify-items: center;
        flex-direction: column;
        padding: 12px;
      }
      
      .entry {
        display: flex;
        flex-direction: row;
        justify-content: center;
        align-items: center;
        padding-top: 12px;
        margin-bottom: 12px;
        border-top: 1px solid var(--divider-color);
      }

      .entry:first-child {
        border-top: none;
      }

      .entry ha-form {
        flex: 1;
      }

      ha-button ha-svg-icon {
        color: inherit;
      }

      ha-svg-icon, ha-icon-button {
        color: var(--secondary-text-color);
      }
    `;}};__decorate([n$1({attribute:false})],MCG_List.prototype,"hass",void 0);__decorate([n$1({attribute:false})],MCG_List.prototype,"data",void 0);__decorate([n$1({attribute:false})],MCG_List.prototype,"schema",void 0);__decorate([n$1({attribute:false})],MCG_List.prototype,"computeLabel",void 0);__decorate([n$1({type:Boolean})],MCG_List.prototype,"disabled",void 0);MCG_List=__decorate([t$1("ha-form-mcg-list")],MCG_List);

let HaFormMCGTemplate=class HaFormMCGTemplate extends i$2{constructor(){super(...arguments);this.disabled=false;this._templateMode=false;}connectedCallback(){super.connectedCallback();const DATA=this.schema.flatten?this.data:{[this.schema.name]:this.data};this._templateMode=isTemplate(DATA[this.schema.name]);}_computeSelector(){return [{name:this.schema.name,label:this.schema.label,selector:this.schema.schema,required:this.schema.required,default:this.schema.default,context:this.schema.context||undefined}];}render(){var _a;const DATA=this.schema.flatten?this.data:{[this.schema.name]:this.data};const dataIsTemplate=(_a=this._templateMode)!==null&&_a!==void 0?_a:isTemplate(DATA[this.schema.name]);let schema=Array.isArray(this.schema.schema)?this.schema.schema:this._computeSelector();if(dataIsTemplate){schema=[{name:this.schema.name,label:this.schema.label,required:this.schema.required,selector:{template:{}}}];}return x`
      <div class="selector-container">
        <ha-form
          .hass=${this.hass}
          .data=${DATA}
          .schema=${schema}
          .computeLabel=${this.computeLabel}
          .disabled=${this.disabled}
          @value-changed=${this._valueChanged}
        >
        </ha-form>
        <ha-button .disabled=${this.disabled} @click=${this._toggleTemplateMode}>
          ${this._templateMode?localize(this.hass,"editor.switch_to_form"):localize(this.hass,"editor.switch_to_template")}
          <ha-svg-icon slot="icon" .path=${this._templateMode?mdiListBoxOutline:mdiCodeBraces}></ha-svg-icon>
        </ha-button>
      </div>
    `;}_toggleTemplateMode(){this._templateMode=!this._templateMode;const value=this.schema.flatten?this.data[this.schema.name]:this.data;if(this._templateMode){const newValue=this.schema.flatten?Object.assign(Object.assign({},this.data),{[this.schema.name]:String(value!==null&&value!==void 0?value:"")}):String(value!==null&&value!==void 0?value:"");fireEvent(this,"value-changed",{value:newValue});}else {if(value===""){const newValue=this.schema.flatten?Object.assign(Object.assign({},this.data),{[this.schema.name]:undefined}):undefined;fireEvent(this,"value-changed",{value:newValue});}}}_valueChanged(ev){ev.stopPropagation();let value=ev.detail.value[this.schema.name];const oldValue=this.schema.flatten?this.data[this.schema.name]:this.data;if(value===oldValue){return;}if(value===""){value=undefined;}const data=this.schema.flatten?{value:Object.assign(Object.assign({},this.data),{[this.schema.name]:value})}:{value:value};fireEvent(this,"value-changed",data);}};HaFormMCGTemplate.styles=i$5`
    :host {
      display: block;
    }
    .selector-container {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    ha-form {
      flex: 1;
      width: 100%;
    }
  `;__decorate([n$1({attribute:false})],HaFormMCGTemplate.prototype,"hass",void 0);__decorate([n$1({attribute:false})],HaFormMCGTemplate.prototype,"data",void 0);__decorate([n$1({attribute:false})],HaFormMCGTemplate.prototype,"schema",void 0);__decorate([n$1({type:Boolean})],HaFormMCGTemplate.prototype,"disabled",void 0);__decorate([n$1({attribute:false})],HaFormMCGTemplate.prototype,"computeLabel",void 0);__decorate([r$1()],HaFormMCGTemplate.prototype,"_templateMode",void 0);HaFormMCGTemplate=__decorate([t$1("ha-form-mcg-template")],HaFormMCGTemplate);

let ModernCircularGaugeEditor=class ModernCircularGaugeEditor extends i$2{constructor(){super(...arguments);this._schema=memoizeOne((showInnerGaugeOptions,showTertiaryGaugeOptions)=>[{name:"entity",type:"mcg-template",required:true,schema:{entity:{domain:NUMBER_ENTITY_DOMAINS}}},{name:"name",type:"mcg-template",schema:{text:{}}},{name:"",type:"grid",schema:[{name:"icon",type:"mcg-template",flatten:true,schema:{icon:{}},context:{icon_entity:"entity"}},{name:"unit",selector:{text:{}}},{name:"min",type:"mcg-template",default:DEFAULT_MIN,schema:{number:{step:0.1}}},{name:"max",type:"mcg-template",default:DEFAULT_MAX,schema:{number:{step:0.1}}}]},{name:"primary_entity_style",type:"expandable",flatten:true,iconPath:mdiGauge,schema:getEntityStyleSchema(true,RADIUS$1,"primary_label")},getSecondarySchema(showInnerGaugeOptions),getTertiarySchema(showTertiaryGaugeOptions),{name:"appearance",type:"expandable",flatten:true,iconPath:mdiPalette,schema:[{name:"header_position",default:"bottom",selector:{select:{options:[{label:"Bottom",value:"bottom"},{label:"Top",value:"top"}],translation_key:"header_position_options",mode:"box"}}},{name:"",type:"grid",schema:[{name:"smooth_segments",selector:{boolean:{}}},{name:"show_header",default:true,selector:{boolean:{}}},{name:"show_icon",default:true,selector:{boolean:{}}},{name:"adaptive_icon_color",default:false,selector:{boolean:{}}},{name:"icon_entity",default:"primary",helper:"icon_entity",selector:{select:{options:[{value:"primary",label:"Primary"},{value:"secondary",label:"Secondary"},{value:"tertiary",label:"Tertiary"}],mode:"dropdown",translation_key:"icon_entity_options"}}}]}]},{name:"segments",type:"mcg-list",iconPath:mdiSegment,schema:[{name:"",type:"grid",column_min_width:"100px",schema:[{name:"from",type:"mcg-template",required:true,schema:{number:{step:0.1}}},{name:"color",type:"mcg-template",required:true,schema:{color_rgb:{}}}]},{name:"label",type:"mcg-template",schema:{text:{}}}]},{name:"tap_action",selector:{ui_action:{}}}]);this._localizeValue=key=>{return localize(this.hass,`editor.${key}`);};this._computeLabel=schema=>{var _a;return ((_a=this.hass)===null||_a===void 0?void 0:_a.localize(`ui.panel.lovelace.editor.card.generic.${schema.name}`))||localize(this.hass,`editor.${schema.name}`);};this._computeHelper=schema=>{if("helper"in schema){return localize(this.hass,`editor.helper.${schema.helper}`);}return undefined;};}setConfig(config){let secondary=config.secondary;if(secondary===undefined&&config.secondary_entity!==undefined){secondary=config.secondary_entity;}if(typeof secondary==="object"){const template=secondary.template||"";if(template.length>0){secondary=template;}}this._config=Object.assign(Object.assign({},config),{secondary:secondary,secondary_entity:undefined});}render(){var _a,_b;if(!this.hass||!this._config){return E;}const schema=this._schema(typeof this._config.secondary!="string"&&((_a=this._config.secondary)===null||_a===void 0?void 0:_a.show_gauge)=="inner",typeof this._config.tertiary!="string"&&((_b=this._config.tertiary)===null||_b===void 0?void 0:_b.show_gauge)=="inner");const DATA=Object.assign({},this._config);return x`
    <ha-form
        .hass=${this.hass}
        .data=${DATA}
        .schema=${schema}
        .computeLabel=${this._computeLabel}
        .localizeValue=${this._localizeValue}
        .computeHelper=${this._computeHelper}
        @value-changed=${this._valueChanged}
    ></ha-form>
    `;}_valueChanged(ev){var _a;let config=ev.detail.value;if(!config){return;}let newSecondary={};if(typeof((_a=this._config)===null||_a===void 0?void 0:_a.secondary)==="string"){newSecondary=Object.assign(Object.assign({},newSecondary),{entity:this._config.secondary});}if(typeof config.secondary==="object"){Object.entries(config.secondary).forEach(([key,value])=>{if(isNaN(Number(key))){newSecondary=Object.assign(Object.assign({},newSecondary),{[key]:value});}});}config.secondary=newSecondary;fireEvent(this,"config-changed",{config});}static get styles(){return i$5`
    `;}};__decorate([n$1({attribute:false})],ModernCircularGaugeEditor.prototype,"hass",void 0);__decorate([r$1()],ModernCircularGaugeEditor.prototype,"_config",void 0);ModernCircularGaugeEditor=__decorate([t$1("modern-circular-gauge-editor")],ModernCircularGaugeEditor);

var mcgEditor = /*#__PURE__*/Object.freeze({
    __proto__: null,
    get ModernCircularGaugeEditor () { return ModernCircularGaugeEditor; }
});

const FORM=[{name:"entity",type:"mcg-template",required:true,schema:{entity:{domain:NUMBER_ENTITY_DOMAINS}}},{name:"name",type:"mcg-template",schema:{text:{}}},{name:"",type:"grid",schema:[{name:"icon",type:"mcg-template",flatten:true,schema:{icon:{}},context:{icon_entity:"entity"}},{name:"unit",selector:{text:{}}},{name:"min",type:"mcg-template",default:DEFAULT_MIN,schema:{number:{step:0.1}}},{name:"max",type:"mcg-template",default:DEFAULT_MAX,schema:{number:{step:0.1}}}]},{name:"badge_appearance",type:"expandable",iconPath:mdiPalette,flatten:true,schema:[{name:"",type:"grid",schema:[{name:"needle",selector:{boolean:{}}},{name:"show_name",default:false,selector:{boolean:{}}},{name:"show_state",default:true,selector:{boolean:{}}},{name:"show_unit",default:true,selector:{boolean:{}}},{name:"show_icon",default:true,selector:{boolean:{}}},{name:"smooth_segments",selector:{boolean:{}}},{name:"start_from_zero",helper:"start_from_zero",selector:{boolean:{}}}]},{name:"state_text",helper:"state_text",selector:{template:{}}},{name:"gauge_foreground_style",type:"expandable",iconPath:mdiFlipToFront,schema:getGaugeStyleSchema(14)},{name:"gauge_background_style",type:"expandable",iconPath:mdiFlipToBack,schema:getGaugeStyleSchema(14)}]},{name:"segments",type:"mcg-list",iconPath:mdiSegment,schema:[{name:"",type:"grid",column_min_width:"100px",schema:[{name:"from",type:"mcg-template",required:true,schema:{number:{step:0.1}}},{name:"color",type:"mcg-template",required:true,schema:{color_rgb:{}}}]}]},{name:"tap_action",selector:{ui_action:{}}}];let ModernCircularGaugeBadgeEditor=class ModernCircularGaugeBadgeEditor extends i$2{constructor(){super(...arguments);this._computeLabel=schema=>{var _a;return ((_a=this.hass)===null||_a===void 0?void 0:_a.localize(`ui.panel.lovelace.editor.card.generic.${schema.name}`))||localize(this.hass,`editor.${schema.name}`);};this._computeHelper=schema=>{if("helper"in schema){return localize(this.hass,`editor.helper.${schema.helper}`);}return undefined;};}setConfig(config){this._config=config;}render(){var _a;if(!this.hass||!this._config){return E;}const DATA=Object.assign(Object.assign({},this._config),{segments:(_a=this._config.segments)===null||_a===void 0?void 0:_a.map(value=>{let color=value.color;if(typeof value.color==="string"){color=hexToRgb(value.color);}return Object.assign(Object.assign({},value),{color});})});return x`
    <ha-form
      .hass=${this.hass}
      .data=${DATA}
      .schema=${FORM}
      .computeLabel=${this._computeLabel}
      .computeHelper=${this._computeHelper}
      @value-changed=${this._valueChanged}
    ></ha-form>
    `;}_valueChanged(ev){let config=ev.detail.value;if(!config){return;}fireEvent(this,"config-changed",{config});}static get styles(){return i$5`
    `;}};__decorate([n$1({attribute:false})],ModernCircularGaugeBadgeEditor.prototype,"hass",void 0);__decorate([r$1()],ModernCircularGaugeBadgeEditor.prototype,"_config",void 0);ModernCircularGaugeBadgeEditor=__decorate([t$1("modern-circular-gauge-badge-editor")],ModernCircularGaugeBadgeEditor);

var gaugeBadgeEditor = /*#__PURE__*/Object.freeze({
    __proto__: null,
    get ModernCircularGaugeBadgeEditor () { return ModernCircularGaugeBadgeEditor; }
});
