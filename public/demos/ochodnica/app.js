const routes=[...document.querySelectorAll('[data-route]')];
const pages=[...document.querySelectorAll('[data-page]')];
const mainNav=document.getElementById('mainNav');
const menuButton=document.getElementById('menuButton');
const govInfoButton=document.getElementById('govInfoButton');
const govInfo=document.getElementById('govInfo');
const contrastButton=document.getElementById('contrastButton');

function showPage(route){
  const target=pages.find(p=>p.dataset.page===route) || pages.find(p=>p.dataset.page==='domov');
  pages.forEach(p=>p.classList.toggle('is-active',p===target));
  routes.forEach(link=>{
    if(link.closest('.main-nav')){
      if(link.dataset.route===target.dataset.page) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    }
  });
  mainNav.classList.remove('is-open');
  menuButton?.setAttribute('aria-expanded','false');
  window.scrollTo({top:0,behavior:'smooth'});
  document.title=`Ochodnica – ${target.dataset.page==='domov'?'demo webu podľa IDSK 3':target.querySelector('h1')?.textContent || 'demo'}`;
}

routes.forEach(link=>link.addEventListener('click',e=>{
  e.preventDefault();
  const route=link.dataset.route;
  history.pushState({route},'',`#${route}`);
  showPage(route);
}));

menuButton?.addEventListener('click',()=>{
  const open=mainNav.classList.toggle('is-open');
  menuButton.setAttribute('aria-expanded',String(open));
});

govInfoButton?.addEventListener('click',()=>{
  const expanded=govInfoButton.getAttribute('aria-expanded')==='true';
  govInfoButton.setAttribute('aria-expanded',String(!expanded));
  govInfo.hidden=expanded;
});

contrastButton?.addEventListener('click',()=>{
  const active=document.body.classList.toggle('high-contrast');
  contrastButton.setAttribute('aria-pressed',String(active));
  contrastButton.textContent=active?'Bežný vzhľad':'Kontrast';
});

window.addEventListener('popstate',()=>showPage(location.hash.replace('#','')||'domov'));
showPage(location.hash.replace('#','')||'domov');
