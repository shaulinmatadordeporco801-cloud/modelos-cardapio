# Reset deploy trigger: 2026-02-15 03:22
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import logging

from database import SessionLocal, engine
from models import Base, Category, Product

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sua Empresa")

# Montagem de arquivos estáticos (servindo tudo da raiz)
app.mount("/static", StaticFiles(directory="."), name="static")

# Inicialização do Banco de Dados no Startup
@app.on_event("startup")
def startup_db_client():
    logger.info("🔍 Verificando conexão com o banco de dados...")
    try:
        # Tenta criar as tabelas se não existirem
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Banco de dados pronto.")
    except Exception as e:
        logger.error(f"❌ ERRO CRÍTICO NA CONEXÃO: {e}")

# Dependência para o banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota Admin Toggle
@app.post("/admin/toggle/{product_id}")
async def toggle_product_availability(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_available = not product.is_available
    db.commit()
    return {"status": "success", "is_available": product.is_available}

# Helper to render Logo (SVG)
def render_logo(size="md", classes=""):
    return ""

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    try:
        # Order categories manually to guarantee the pyramid layout
        all_categories = db.query(Category).all()
        pref_order = {"Espetinho": 1, "Bebidas": 2, "Acompanhamentos": 3, "Drinks": 4}
        categories = sorted(all_categories, key=lambda c: pref_order.get(c.name, 99))
        
        products = db.query(Product).all()
        
        # Pre-process data for the view
        categories_data = []
        
        # Aba "Todos" no início
        all_prods = products
        # Criar um objeto de categoria "virtual" para o "Todos"
        all_cat = type('obj', (object,), {"id": "all", "name": "Todos"})
        categories_data.append({"category": all_cat, "products": all_prods})
        
        for cat in categories:
            prods = [p for p in products if p.category_id == cat.id]
            categories_data.append({"category": cat, "products": prods})
        
        # Default active tab (primeira é "Todos")
        first_cat_id = "all"
        
        # Build tabs buttons HTML
        tabs_btns_html = ""
        for i, item in enumerate(categories_data):
            cat = item['category']
            is_active = (cat.id == first_cat_id)
            btn_class = "bg-brand-orange text-white shadow-[0_5px_15px_rgba(255,107,0,0.2)]" if is_active else "text-neutral-400 hover:bg-brand-orange/10 hover:text-brand-orange"
            
            # Pyramid layout: Todos, Espetinho e Bebidas no topo (w-1/2 approx), outros base
            if cat.name in ["Todos", "Espetinho", "Bebidas"]:
                mobile_class = "w-[48%] md:w-auto"
            else:
                mobile_class = "w-full md:w-auto"
                
            tabs_btns_html += f"""
            <button onclick="switchTab('{cat.id}')" 
                    id="tab-btn-{cat.id}"
                    class="tab-btn {mobile_class} flex items-center justify-center text-[10px] md:text-xs font-bold uppercase tracking-wider px-2 md:px-8 py-3.5 md:py-4 rounded-lg transition-all duration-300 active:scale-95 shadow-sm {btn_class}">
              {cat.name}
            </button>
            """

        # Build items content HTML
        tabs_content_html = ""
        for item in categories_data:
            cat = item['category']
            prods = item['products']
            is_active = (cat.id == first_cat_id)
            content_class = "active" if is_active else ""
            
            subcat_filter_html = ""
            if cat.name == 'Bebidas':
                subcat_filter_html = """
                <div class="flex flex-wrap gap-2 mb-10 reveal-on-scroll">
                    <button onclick="filterSubCat('all')" class="subcat-btn active px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-orange/20 transition-all bg-brand-orange text-white">Todos</button>
                    <button onclick="filterSubCat('Cervejas')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-orange/20 transition-all text-neutral-400 hover:bg-brand-orange/5">Cervejas</button>
                    <button onclick="filterSubCat('Refrigerantes')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-orange/20 transition-all text-neutral-400 hover:bg-brand-orange/5">Refrigerantes</button>
                    <button onclick="filterSubCat('Águas')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-orange/20 transition-all text-neutral-400 hover:bg-brand-orange/5">Águas</button>
                </div>
                """

            products_grid_html = ""
            for prod in prods:
                avail_class = "opacity-50 grayscale select-none" if not prod.is_available else ""
                badge_class = "" if not prod.is_available else "hidden"
                
                # Resgate do nome da categoria original
                if cat.id == "all":
                    original_cat = db.query(Category).filter(Category.id == prod.category_id).first()
                    display_cat_name = original_cat.name if original_cat else ""
                else:
                    display_cat_name = cat.name

                # Image / Placeholder logic
                if prod.image_url:
                    img_content = f'<img src="{prod.image_url}" alt="{prod.name}" class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />'
                else:
                    img_content = f"""
                    <div class="w-full h-full bg-neutral-100 dark:bg-neutral-800 flex items-center justify-center border-2 border-dashed border-neutral-300 dark:border-neutral-700">
                        <span class="font-bebas text-lg md:text-2xl text-neutral-400 dark:text-neutral-500 tracking-widest text-center px-4">FOTO DO SEU PRODUTO</span>
                    </div>
                    """

                img_html = f"""
                <div class="relative aspect-[4/3] overflow-hidden">
                    {img_content}
                    <div class="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent opacity-40"></div>
                </div>
                """
                
                admin_btn_color = "text-red-500" if prod.is_available else "text-green-500"

                products_grid_html += f"""
                <div id="product-card-{prod.id}" 
                     class="product-card reveal-on-scroll group bg-neutral-900/60 backdrop-blur-md border border-brand-orange/10 dark:border-white/5 overflow-hidden transition-all duration-1000 hover:shadow-[0_25px_50px_-12px_rgba(255,107,0,0.15)] hover:border-brand-orange/40 dark:hover:border-brand-orange/40 rounded-xl flex flex-col relative {avail_class}">
                    <div class="absolute inset-0 pointer-events-none glass-shimmer opacity-30"></div>
                    
                    <div id="status-badge-{prod.id}" class="absolute top-2 left-2 z-20 px-2 py-0.5 rounded text-[8px] md:text-[10px] font-black uppercase tracking-widest shadow-lg transition-all {badge_class} bg-red-500 text-white">
                        ESGOTADO
                    </div>

                    <div class="admin-only hidden absolute bottom-4 left-4 z-[30] flex gap-2">
                        <button onclick="toggleAvailability({prod.id})" class="p-2 bg-neutral-800/90 rounded-lg shadow-xl border border-brand-orange/20 hover:scale-110 active:scale-95 transition-all group/admin-btn">
                            <svg class="w-4 h-4 {admin_btn_color}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                        </button>
                    </div>

                    {img_html}
                    
                    <div class="p-6 md:p-8 flex flex-col flex-grow">
                        <div class="flex justify-between items-start mb-2">
                            <span class="text-[8px] font-black uppercase tracking-[0.3em] text-brand-orange">{display_cat_name}</span>
                            <span class="text-brand-orange font-bebas text-lg md:text-2xl ml-2">R$ {prod.price:.2f}</span>
                        </div>
                        <h4 class="font-bebas text-2xl md:text-3xl tracking-wide text-neutral-100 group-hover:text-brand-orange transition-colors line-clamp-1 mb-2">{prod.name}</h4>
                        <p class="text-[10px] md:text-sm text-neutral-400 font-light leading-relaxed line-clamp-2">{prod.description or ""}</p>
                    </div>
                </div>
                """

            tabs_content_html += f"""
            <div id="tab-content-{cat.id}" class="tab-content {content_class}">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-10">
                    {products_grid_html}
                </div>
            </div>
            """

    except Exception as e:
        logger.error(f"Erro ao carregar cardápio: {e}")
        return HTMLResponse(content=f"Erro ao carregar o site: {e}", status_code=500)

    logo_md = render_logo(size="md")
    logo_sm = render_logo(size="sm")

    html_content = f"""<!DOCTYPE html>
    <html lang="pt-BR" class="scroll-smooth">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Sua Empresa | Cardápio Digital</title>
        <!-- Version: 1.0.6 - Manual Sort Build -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
          tailwind.config = {{
            darkMode: 'class',
            theme: {{
              extend: {{
                colors: {{
                  'rich-black': '#121212', 
                  'brand-orange': '#FF6B00', 
                  'brand-orange-light': '#FFF0E6', 
                  'steak-gold': '#D4AF37',
                  'smoke-grey': '#1A1A1A', 
                  'dark-text': '#F3F4F6', 
                  'medium-text': '#A1A1AA',
                }},
                fontFamily: {{
                  bebas: ['"Bebas Neue"', 'cursive'],
                  montserrat: ['Montserrat', 'sans-serif'],
                }},
                animation: {{ 'shimmer': 'shimmer 3s infinite linear', 'fadeIn': 'fadeIn 0.5s ease-out' }},
                keyframes: {{
                  shimmer: {{ '0%': {{ transform: 'translateX(-100%)' }}, '100%': {{ transform: 'translateX(100%)' }} }},
                  fadeIn: {{ '0%': {{ opacity: '0', transform: 'translateY(10px)' }}, '100%': {{ opacity: '1', transform: 'translateY(0)' }} }}
                }}
              }}
            }}
          }}
        </script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
        <style>
          .glass-shimmer::after {{ content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%; background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.4), transparent); transform: skewX(-25deg); animation: shimmer 4s infinite; }}
          .tab-content {{ display: none; }}
          .tab-content.active {{ display: block; }}
          
          /* Aurora Boreal Effect */
          /* EMBERS ANIMATION */
          .embers-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1;
            background: radial-gradient(circle at bottom, rgba(255,107,0,0.05) 0%, transparent 70%);
          }}
          
          .ember {{
            position: absolute;
            bottom: -20px;
            background: #FF6B00;
            border-radius: 50%;
            filter: blur(1px);
            opacity: 0.6;
            animation: rise linear infinite;
          }}

          @keyframes rise {{
            0% {{ transform: translateY(0) scale(1); opacity: 0.6; }}
            100% {{ transform: translateY(-100vh) scale(0.5); opacity: 0; }}
          }}

          .wood-texture {{
            background-image: url('https://www.transparenttextures.com/patterns/dark-wood.png');
            opacity: 0.05;
          }}
          
          .dark .rich-black-bg {{ background-color: #0a0a0a; }}
          .dark .dark-text-color {{ color: #f3f4f6; }}
          .dark .nav-glass {{ background-color: rgba(15, 15, 15, 0.8); border-color: rgba(255, 255, 255, 0.05); }}
          
          body {{ background-color: #121212; color: #F3F4F6; }}
          
          /* Hide scrollbar for Chrome, Safari and Opera */
          .no-scrollbar::-webkit-scrollbar {{ display: none; }}
          /* Hide scrollbar for IE, Edge and Firefox */
          .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
        </style>
        <script>
            function applyTheme() {{
                try {{
                    const theme = localStorage.getItem('theme');
                    const isDark = theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
                    if (isDark) {{
                        document.documentElement.classList.add('dark');
                    }} else {{
                        document.documentElement.classList.remove('dark');
                    }}
                }} catch (e) {{
                    console.error('Theme apply error:', e);
                }}
            }}
            applyTheme();
        </script>
    </head>
    <body class="font-montserrat overflow-x-hidden selection:bg-brand-orange selection:text-white transition-colors duration-500 bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
        
        <!-- EMBERS BACKGROUND -->
        <div class="embers-container" id="embers"></div>
        <div class="fixed inset-0 wood-texture pointer-events-none z-[1]"></div>

        <nav class="fixed top-0 left-0 w-full z-[100] bg-neutral-900/80 backdrop-blur-xl border-b border-white/5 py-3 md:py-4 px-6 md:px-12 flex justify-between items-center shadow-sm transition-colors duration-300">
          <div class="flex items-center gap-3 group cursor-pointer relative z-[110]">
            <div class="flex flex-col">
              <span class="font-bebas text-xl md:text-2xl tracking-wider leading-none text-white">Sua Empresa</span>
              <span class="text-[9px] md:text-[10px] text-brand-orange tracking-[0.2em] font-bold uppercase leading-none mt-1">Cardápio Digital</span>
            </div>
          </div>
          <div class="flex gap-4 md:gap-10 items-center uppercase text-[11px] font-bold tracking-[0.3em] text-dark-text/80 dark:text-white/80">
            <div class="hidden md:flex gap-10">
              <a href="#hero" class="hover:text-brand-orange transition-all relative group">Início</a>
              <a href="#menu" class="hover:text-brand-orange transition-all relative group">Cardápio</a>
              <a href="#location" class="hover:text-brand-orange transition-all relative group">Localização</a>
            </div>
            <div class="relative">
              <button onclick="toggleSettingsMenu()" class="p-2.5 bg-neutral-100 dark:bg-neutral-800 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-all focus:outline-none"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg></button>
              <div id="settings-menu" class="absolute right-0 mt-3 w-56 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-2xl p-4 opacity-0 invisible transition-all z-[200]">
                <div class="flex items-center justify-between p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-xl cursor-pointer" onclick="toggleDarkMode()">
                  <span class="text-xs font-semibold text-neutral-900 dark:text-neutral-100">Modo Escuro</span>
                  <div class="w-10 h-5 bg-neutral-200 dark:bg-neutral-700 rounded-full relative"><div id="theme-toggle-indicator" class="absolute top-1 left-1 w-3 h-3 bg-brand-orange rounded-full transition-all dark:translate-x-5"></div></div>
                </div>
                <div class="h-[1px] bg-neutral-100 dark:bg-neutral-800 my-2"></div>
                <div id="admin-login-section" class="flex items-center justify-between p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-xl cursor-pointer" onclick="showAdminLogin()"><span class="text-xs font-semibold text-neutral-900 dark:text-neutral-100">Admin</span></div>
                <div id="admin-active-section" class="hidden flex items-center justify-between p-2 hover:bg-red-50 rounded-xl cursor-pointer" onclick="logoutAdmin()"><span class="text-xs font-semibold text-red-600">Sair Admin</span></div>
              </div>
            </div>
          </div>
        </nav>
        
        <div id="admin-modal" class="fixed inset-0 z-[200] hidden bg-black/80 backdrop-blur-md flex items-center justify-center p-6">
            <div class="bg-neutral-900 w-full max-w-md rounded-3xl p-8 shadow-2xl border border-brand-orange/20">
                <h3 class="font-bebas text-4xl mb-2 text-brand-orange uppercase tracking-widest">Acesso Restrito</h3>
                <p class="text-neutral-400 text-xs mb-8 uppercase tracking-widest font-bold">Portal do Mestre Churrasqueiro</p>
                <input type="password" id="admin-password" placeholder="••••••" class="w-full bg-neutral-800 border border-white/5 rounded-2xl p-5 text-center text-3xl mb-8 focus:border-brand-orange/50 focus:outline-none transition-all placeholder:opacity-20 text-white">
                <div class="flex gap-4">
                    <button onclick="closeAdminModal()" class="flex-1 font-bold text-neutral-500 hover:text-white transition-colors uppercase tracking-widest text-xs">Voltar</button>
                    <button onclick="attemptAdminLogin()" class="flex-1 bg-brand-orange text-white py-4 rounded-2xl font-bold uppercase tracking-widest text-xs shadow-lg shadow-brand-orange/20 hover:scale-[1.02] active:scale-95 transition-all">Desbloquear</button>
                </div>
            </div>
        </div>

        <section id="hero" class="relative min-h-screen flex items-center justify-center pt-24 overflow-hidden">
            <div class="absolute inset-0 z-0">
                <img src="https://images.unsplash.com/photo-1594041680534-e8c8cdebd679?auto=format&fit=crop&q=80&w=2000" class="w-full h-full object-cover opacity-40" />
                <div class="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-900/60 to-transparent"></div>
            </div>
            <div class="relative z-10 container mx-auto px-6 text-center">
                <h1 class="font-bebas text-[clamp(2.5rem,12vw,8rem)] leading-[0.85] mb-8 text-neutral-100"><span class="text-brand-orange">SUA EMPRESA</span></h1>
                <p class="max-w-2xl mx-auto text-base md:text-2xl text-neutral-300 font-light mb-16">Qualidade e sabor em cada detalhe.</p>
                <div class="flex flex-col items-center gap-4"><div class="h-20 w-[1px] bg-brand-orange"></div><span class="uppercase tracking-[0.4em] text-[10px] md:text-xs">Cardápio abaixo</span></div>
            </div>
        </section>

        <section id="menu" class="py-24 relative bg-transparent">
            <div class="container mx-auto px-4">
                <div class="text-center mb-16">
                   <h2 class="font-bebas text-5xl md:text-8xl mb-10 text-neutral-100 uppercase">Saboreie momentos em <span class="text-brand-orange">família.</span></h2>
                    <div class="flex flex-wrap justify-center gap-2 bg-brand-orange/5 p-2 rounded-xl max-w-4xl mx-auto mb-12">
                       {tabs_btns_html}
                    </div>
                </div>
                {tabs_content_html}
            </div>
        </section>

        <section id="location" class="py-32 bg-neutral-950 overflow-hidden relative">
          <div class="container mx-auto px-6 relative z-10">
            <div class="flex flex-col lg:flex-row gap-20 items-center">
              <div class="w-full lg:w-1/2">
                <h2 class="font-bebas text-6xl md:text-8xl mb-8">ONDE A <span class="text-brand-orange">BRASA</span> VIVE</h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-12">
                   <div class="flex gap-5 items-start"><div class="p-4 bg-brand-orange/5 rounded-2xl"><svg class="w-6 h-6 text-brand-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg></div><div><h4 class="font-bold uppercase text-[10px] tracking-[0.3em] mb-3">Endereço</h4><p class="text-sm">Rua x, 000<br/>Cidade x</p></div></div>
                   <div class="flex gap-5 items-start"><div class="p-4 bg-brand-orange/5 rounded-2xl"><svg class="w-6 h-6 text-brand-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div><div><h4 class="font-bold uppercase text-[10px] tracking-[0.3em] mb-3">Horário</h4><p class="text-sm">Segunda a Sábado<br/>17:30 às 22:30</p></div></div>
                </div>
              </div>
              <div class="w-full lg:w-1/2 h-[500px] shadow-2xl rounded-3xl overflow-hidden bg-brand-orange/5 flex items-center justify-center border-4 border-dashed border-brand-orange/20">
                <p class="font-bebas text-2xl text-brand-orange opacity-50 uppercase tracking-widest text-center px-10">Localização Privada<br/><span class="text-xs font-montserrat">Mapa removido por segurança</span></p>
              </div>
            </div>
          </div>
        </section>

        <footer class="bg-neutral-950 border-t border-white/5 py-16 px-6 text-center">
           <div class="container mx-auto flex flex-col items-center gap-10">
              <div class="text-center">
                 <p class="font-bold uppercase tracking-[0.4em] mb-4">Aberto para você</p>
                 <p class="text-neutral-500 text-xs font-medium">Contatos: xxxx-xxxx<br/>© 2026</p>
              </div>
           </div>
        </footer>

        <script>
            function toggleSettingsMenu() {{
                const menu = document.getElementById('settings-menu');
                menu.classList.toggle('opacity-0');
                menu.classList.toggle('invisible');
            }}

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {{
                const btn = document.querySelector('button[onclick="toggleSettingsMenu()"]');
                const menu = document.getElementById('settings-menu');
                if (btn && menu && !btn.contains(e.target) && !menu.contains(e.target)) {{
                    menu.classList.add('opacity-0', 'invisible');
                }}
            }});

            function toggleDarkMode() {{
                const html = document.documentElement;
                if (html.classList.contains('dark')) {{
                    localStorage.setItem('theme', 'light');
                }} else {{
                    localStorage.setItem('theme', 'dark');
                }}
                applyTheme();
            }}

            const ADMIN_TOKEN = "admin_logged_in";
            function showAdminLogin() {{ document.getElementById('admin-modal').classList.remove('hidden'); document.getElementById('admin-password').focus(); }}
            function closeAdminModal() {{ document.getElementById('admin-modal').classList.add('hidden'); document.getElementById('admin-password').value = ''; }}
            function attemptAdminLogin() {{
                if (document.getElementById('admin-password').value === "230923") {{
                    localStorage.setItem(ADMIN_TOKEN, "true");
                    updateAdminUI(); closeAdminModal();
                }} else alert("Código incorreto!");
            }}
            function logoutAdmin() {{ localStorage.removeItem(ADMIN_TOKEN); location.reload(); }}
            function updateAdminUI() {{
                if (localStorage.getItem(ADMIN_TOKEN) === "true") {{
                    document.getElementById('admin-login-section').classList.add('hidden');
                    document.getElementById('admin-active-section').classList.remove('hidden');
                    document.querySelectorAll('.admin-only').forEach(el => el.classList.remove('hidden'));
                }}
            }}

            async function toggleAvailability(id) {{
                const res = await fetch(`/admin/toggle/${{id}}`, {{ method: 'POST' }});
                const data = await res.json();
                if (data.status === 'success') {{
                    const card = document.getElementById(`product-card-${{id}}`);
                    const b = document.getElementById(`status-badge-${{id}}`);
                    if (data.is_available) {{ card.classList.remove('opacity-50', 'grayscale', 'select-none'); b.classList.add('hidden'); }}
                    else {{ card.classList.add('opacity-50', 'grayscale', 'select-none'); b.classList.remove('hidden'); }}
                }}
            }}

            function switchTab(id) {{
                document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('bg-brand-orange', 'text-white', 'shadow-[0_5px_15px_rgba(255,107,0,0.2)]'));
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.add('text-neutral-400', 'hover:bg-brand-orange/10', 'hover:text-brand-orange'));
                
                const activeBtn = document.getElementById('tab-btn-' + id);
                activeBtn.classList.add('bg-brand-orange', 'text-white', 'shadow-[0_5px_15px_rgba(255,107,0,0.2)]');
                activeBtn.classList.remove('text-neutral-400', 'hover:bg-brand-orange/10', 'hover:text-brand-orange');
                
                document.getElementById('tab-content-' + id).classList.add('active');
                filterSubCat('all');
            }}

            function filterSubCat(s) {{
                document.querySelectorAll('.subcat-btn').forEach(b => {{
                    if (b.innerText.toLowerCase() === s.toLowerCase() || (s === 'all' && b.innerText === 'Todos')) b.classList.add('bg-brand-orange', 'text-white');
                    else b.classList.remove('bg-brand-orange', 'text-white');
                }});
                document.querySelectorAll('.product-card').forEach(c => {{
                    c.style.display = (s === 'all' || c.getAttribute('data-subcat') === s) ? 'flex' : 'none';
                }});
                if (window.ScrollTrigger) ScrollTrigger.refresh();
            }}

            // Create Embers
            function createEmbers() {{
                const container = document.getElementById('embers');
                if (!container) return;
                
                for (let i = 0; i < 50; i++) {{
                    const ember = document.createElement('div');
                    ember.className = 'ember';
                    
                    const size = Math.random() * 4 + 1;
                    const left = Math.random() * 100;
                    const duration = Math.random() * 10 + 5;
                    const delay = Math.random() * 10;
                    
                    ember.style.width = `${{size}}px`;
                    ember.style.height = `${{size}}px`;
                    ember.style.left = `${{left}}%`;
                    ember.style.animationDuration = `${{duration}}s`;
                    ember.style.animationDelay = `${{delay}}s`;
                    
                    ember.style.opacity = document.documentElement.classList.contains('dark') ? '0.6' : '0.2';
                    container.appendChild(ember);
                }}
            }}

            document.addEventListener("DOMContentLoaded", () => {{
                if (window.gsap) {{
                   gsap.registerPlugin(ScrollTrigger);
                   gsap.utils.toArray('.reveal-on-scroll').forEach(s => gsap.fromTo(s, {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 1, scrollTrigger: {{ trigger: s, start: 'top 90%' }} }}));
                }}
                updateAdminUI();
                createEmbers();
            }});
        </script>
    </body>
    </html>
    """
    return HTMLContent(html_content)

class HTMLContent(HTMLResponse):
    def __init__(self, content: str, status_code: int = 200):
        # Limpeza agressiva de qualquer espaço ou caractere invisível no início do conteúdo
        clean_content = content.lstrip()
        super().__init__(content=clean_content, status_code=status_code)
