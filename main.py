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

app = FastAPI(title="Campeão do Churrasco")

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
    size_classes = {
        "sm": "w-12 h-12",
        "md": "w-20 h-20",
        "lg": "w-32 h-32"
    }
    s_class = size_classes.get(size, "w-20 h-20")
    
    return f"""
    <div class="relative flex items-center justify-center bg-brand-blue shadow-xl overflow-hidden rounded-xl {s_class} {classes}">
      <svg viewBox="0 0 100 100" class="w-[90%] h-[90%] select-none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <path id="textArc" d="M 20,48 A 30,30 0 0,1 80,48" fill="none" />
        </defs>
        <text class="fill-white font-bold" style="font-size: 9px; letter-spacing: 0.12em">
          <textPath href="#textArc" startOffset="50%" text-anchor="middle">CAMPEÃO</textPath>
        </text>
        <text x="50" y="48" text-anchor="middle" class="fill-white font-bold" style="font-size: 5.5px; letter-spacing: 0.05em">DO</text>
        <text x="50" y="62" text-anchor="middle" class="fill-white font-black" style="font-size: 13.5px; letter-spacing: -0.02em">CHURRASCO</text>
        <line x1="22" y1="67" x2="78" y2="67" stroke="white" stroke-width="1.2" />
        <text x="50" y="74" text-anchor="middle" class="fill-white font-bold" style="font-size: 4.8px; letter-spacing: 0.15em">DESDE 1980</text>
      </svg>
    </div>
    """

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
        for cat in categories:
            prods = [p for p in products if p.category_id == cat.id]
            categories_data.append({"category": cat, "products": prods})
        
        # Default active tab (first one)
        first_cat_id = categories[0].id if categories else 0
        
        # Build tabs buttons HTML
        tabs_btns_html = ""
        for item in categories_data:
            cat = item['category']
            is_active = (cat.id == first_cat_id)
            btn_class = "bg-brand-blue text-white shadow-[0_5px_15px_rgba(0,144,255,0.2)]" if is_active else "text-dark-text/40 dark:text-neutral-400 hover:bg-brand-blue/10 hover:text-brand-blue"
            
            # Pyramid layout using stable Flexbox (v1.0.6)
            if cat.name in ["Espetinho", "Bebidas"]:
                # Two buttons sharing the first row
                mobile_class = "w-[48%] md:w-auto"
            else:
                # Full width buttons for the bottom rows (Pyramid base)
                mobile_class = "w-full md:w-auto"
                
            tabs_btns_html += f"""
            <button onclick="switchTab({cat.id})" 
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
                    <button onclick="filterSubCat('all')" class="subcat-btn active px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-blue/20 transition-all bg-brand-blue text-white">Todos</button>
                    <button onclick="filterSubCat('Cervejas')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-blue/20 transition-all text-dark-text/60 dark:text-neutral-400 hover:bg-brand-blue/5">Cervejas</button>
                    <button onclick="filterSubCat('Refrigerantes')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-blue/20 transition-all text-dark-text/60 dark:text-neutral-400 hover:bg-brand-blue/5">Refrigerantes</button>
                    <button onclick="filterSubCat('Águas')" class="subcat-btn px-4 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider border border-brand-blue/20 transition-all text-dark-text/60 dark:text-neutral-400 hover:bg-brand-blue/5">Águas</button>
                </div>
                """

            products_grid_html = ""
            for prod in prods:
                avail_class = "opacity-50 grayscale select-none" if not prod.is_available else ""
                badge_class = "" if not prod.is_available else "hidden"
                img_html = ""
                if prod.image_url:
                    img_html = f"""
                    <div class="relative aspect-video overflow-hidden">
                        <img src="{prod.image_url}" alt="{prod.name}" class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110" />
                        <div class="absolute inset-0 bg-gradient-to-t from-white dark:from-neutral-950 via-transparent to-transparent opacity-40"></div>
                        <div class="absolute top-2 right-2 md:top-4 md:right-4 bg-brand-blue text-white font-bebas text-sm md:text-xl px-2 md:px-4 py-0.5 md:py-1 rounded shadow-lg">R$ {prod.price:.2f}</div>
                    </div>
                    """
                
                admin_btn_color = "text-red-500" if prod.is_available else "text-green-500"
                admin_btn_label = "Desativar" if prod.is_available else "Ativar"

                products_grid_html += f"""
                <div id="product-card-{prod.id}" 
                     data-subcat="{prod.sub_category or ''}"
                     class="product-card reveal-on-scroll group bg-white/60 dark:bg-neutral-900/60 backdrop-blur-md border border-brand-blue/10 dark:border-white/5 overflow-hidden transition-all duration-500 hover:shadow-[0_25px_50px_-12px_rgba(0,144,255,0.15)] hover:border-brand-blue/40 dark:hover:border-brand-blue/40 md:hover:-translate-y-2 rounded-xl flex flex-col relative {avail_class}">
                    <div class="absolute inset-0 pointer-events-none glass-shimmer opacity-30"></div>
                    
                    <div id="status-badge-{prod.id}" class="absolute top-2 left-2 z-20 px-2 py-0.5 rounded text-[8px] md:text-[10px] font-black uppercase tracking-widest shadow-lg transition-all {badge_class} bg-red-500 text-white">
                        ESGOTADO
                    </div>

                    <div class="admin-only hidden absolute top-2 left-2 z-[30] flex gap-2">
                        <button onclick="toggleAvailability({prod.id})" class="p-2 bg-white/90 dark:bg-neutral-800/90 rounded-lg shadow-xl border border-brand-blue/20 hover:scale-110 active:scale-95 transition-all group/admin-btn">
                            <svg class="w-4 h-4 {admin_btn_color}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                            </svg>
                            <span class="absolute top-full left-0 mt-1 bg-dark-text text-white text-[8px] px-1 py-0.5 rounded opacity-0 group-hover/admin-btn:opacity-100 whitespace-nowrap">{admin_btn_label}</span>
                        </button>
                    </div>

                    {img_html}
                    
                    <div class="p-4 md:p-8 flex flex-col flex-grow {'pt-6 md:pt-10' if not prod.image_url else ''}">
                        <div class="flex flex-col md:flex-row justify-between items-start mb-2 md:mb-3 gap-1 md:gap-4">
                          <h4 class="font-bebas text-lg md:text-2xl tracking-wide text-dark-text dark:text-neutral-100 group-hover:text-brand-blue transition-colors line-clamp-2">{prod.name}</h4>
                          {f'<span class="text-brand-blue font-bebas text-base md:text-xl whitespace-nowrap">R$ {prod.price:.2f}</span>' if not prod.image_url else ''}
                        </div>
                        <p class="text-[10px] md:text-xs text-dark-text/50 dark:text-neutral-400 font-light leading-relaxed mb-4 md:mb-6 flex-grow line-clamp-3">{prod.description or ""}</p>
                    </div>
                </div>
                """

            tabs_content_html += f"""
            <div id="tab-content-{cat.id}" class="tab-content {content_class}">
                <div class="mb-16 last:mb-0">
                    <div class="flex items-center gap-4 md:gap-6 mb-8">
                        <h3 class="font-bebas text-3xl md:text-4xl text-brand-blue tracking-widest uppercase">{cat.name}</h3>
                        <div class="flex-grow h-[1px] bg-gradient-to-r from-brand-blue/20 to-transparent"></div>
                    </div>
                    {subcat_filter_html}
                    <div class="grid grid-cols-2 lg:grid-cols-3 gap-3 md:gap-8 product-grid">
                        {products_grid_html}
                    </div>
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
        <title>Campeão do Churrasco | A Arte da Brasa em Mogi Mirim</title>
        <!-- Version: 1.0.6 - Manual Sort Build -->
        <link rel="icon" type="image/png" href="/static/images/Favicon.png?v=1.0.6">
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
                  'rich-black': '#FFFFFF', 
                  'brand-blue': '#0090FF', 
                  'brand-blue-light': '#E0F2FF', 
                  'steak-gold': '#D4AF37',
                  'smoke-grey': '#F3F4F6', 
                  'dark-text': '#0D0D0D', 
                  'medium-text': '#4B5563',
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
          .aurora-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
            opacity: 0;
            transition: opacity 2s ease;
            overflow: hidden;
          }}
          .dark .aurora-container {{ opacity: 0.15; }}
          
          .aurora-blur {{
            position: absolute;
            width: 100%;
            height: 100%;
            background: 
              radial-gradient(circle at 20% 30%, #2dd4bf 0%, transparent 40%),
              radial-gradient(circle at 80% 20%, #3b82f6 0%, transparent 40%),
              radial-gradient(circle at 50% 50%, #a855f7 0%, transparent 50%),
              radial-gradient(circle at 40% 80%, #10b981 0%, transparent 40%);
            filter: blur(80px);
            animation: aurora-morph 15s infinite alternate ease-in-out;
          }}

          @keyframes aurora-morph {{
            0% {{ transform: scale(1) translate(0, 0); opacity: 0.8; }}
            33% {{ transform: scale(1.2) translate(10%, 5%); opacity: 1; }}
            66% {{ transform: scale(0.9) translate(-5%, 10%); opacity: 0.7; }}
            100% {{ transform: scale(1.1) translate(5%, -5%); opacity: 0.9; }}
          }}
          
          .dark .rich-black-bg {{ background-color: #0a0a0a; }}
          .dark .dark-text-color {{ color: #f3f4f6; }}
          .dark .nav-glass {{ background-color: rgba(15, 15, 15, 0.8); border-color: rgba(255, 255, 255, 0.05); }}
          
          /* Hide scrollbar for Chrome, Safari and Opera */
          .no-scrollbar::-webkit-scrollbar {{ display: none; }}
          /* Hide scrollbar for IE, Edge and Firefox */
          .no-scrollbar {{ -ms-overflow-style: none; scrollbar-width: none; }}
        </style>
        <script>
            if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {{
                document.documentElement.classList.add('dark');
            }}
        </script>
    </head>
    <body class="bg-rich-black dark:bg-neutral-950 text-dark-text dark:text-neutral-100 font-montserrat overflow-x-hidden selection:bg-brand-blue selection:text-white transition-colors duration-300">
        
        <!-- AURORA BOREAL BACKGROUND -->
        <div class="aurora-container">
            <div class="aurora-blur"></div>
        </div>

        <nav class="fixed top-0 left-0 w-full z-[100] bg-white/80 dark:bg-neutral-900/80 backdrop-blur-xl border-b border-black/5 dark:border-white/5 py-3 md:py-4 px-6 md:px-12 flex justify-between items-center shadow-sm transition-colors duration-300">
          <div class="flex items-center gap-3 group cursor-pointer relative z-[110]">
            {logo_sm}
            <div class="flex flex-col">
              <span class="font-bebas text-xl md:text-2xl tracking-wider leading-none text-dark-text dark:text-white">Campeão do Churrasco</span>
              <span class="text-[9px] md:text-[10px] text-brand-blue tracking-[0.2em] font-bold uppercase leading-none mt-1">Tradição desde 1980</span>
            </div>
          </div>
          <div class="flex gap-4 md:gap-10 items-center uppercase text-[11px] font-bold tracking-[0.3em] text-dark-text/80 dark:text-white/80">
            <div class="hidden md:flex gap-10">
              <a href="#hero" class="hover:text-brand-blue transition-all relative group">Início</a>
              <a href="#menu" class="hover:text-brand-blue transition-all relative group">Cardápio</a>
              <a href="#location" class="hover:text-brand-blue transition-all relative group">Localização</a>
            </div>
            <div class="relative group/settings">
              <button class="p-2.5 bg-neutral-100 dark:bg-neutral-800 rounded-full hover:bg-neutral-200 dark:hover:bg-neutral-700 transition-all"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg></button>
              <div class="absolute right-0 mt-3 w-56 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-2xl shadow-2xl p-4 opacity-0 invisible group-hover/settings:opacity-100 group-hover/settings:visible transition-all">
                <div class="flex items-center justify-between p-2 hover:bg-neutral-50 dark:hover:bg-neutral-800 rounded-xl cursor-pointer" onclick="toggleDarkMode()">
                  <span class="text-xs font-semibold">Modo Escuro</span>
                  <div class="w-10 h-5 bg-neutral-200 dark:bg-neutral-700 rounded-full relative"><div id="theme-toggle-dot" class="absolute top-1 left-1 w-3 h-3 bg-white dark:bg-brand-blue rounded-full transition-all dark:translate-x-5"></div></div>
                </div>
                <div class="h-[1px] bg-neutral-100 dark:bg-neutral-800 my-2"></div>
                <div id="admin-login-section" class="flex items-center justify-between p-2 hover:bg-neutral-50 rounded-xl cursor-pointer" onclick="showAdminLogin()"><span class="text-xs font-semibold">Admin</span></div>
                <div id="admin-active-section" class="hidden flex items-center justify-between p-2 hover:bg-red-50 rounded-xl cursor-pointer" onclick="logoutAdmin()"><span class="text-xs font-semibold text-red-600">Sair Admin</span></div>
              </div>
            </div>
          </div>
        </nav>
        
        <div id="admin-modal" class="fixed inset-0 z-[200] hidden bg-black/60 backdrop-blur-sm flex items-center justify-center p-6">
            <div class="bg-white dark:bg-neutral-900 w-full max-w-md rounded-3xl p-8 shadow-2xl">
                <h3 class="font-bebas text-3xl mb-4">Acesso Administrativo</h3>
                <input type="password" id="admin-password" class="w-full bg-neutral-100 dark:bg-neutral-800 rounded-2xl p-4 text-center text-2xl mb-6">
                <div class="flex gap-4">
                    <button onclick="closeAdminModal()" class="flex-1 font-bold">Cancelar</button>
                    <button onclick="attemptAdminLogin()" class="flex-1 bg-brand-blue text-white py-4 rounded-2xl font-bold">Entrar</button>
                </div>
            </div>
        </div>

        <section id="hero" class="relative min-h-screen flex items-center justify-center pt-24 overflow-hidden">
            <div class="absolute inset-0 z-0">
                <img src="https://images.unsplash.com/photo-1594041680534-e8c8cdebd679?auto=format&fit=crop&q=80&w=2000" class="w-full h-full object-cover opacity-60 dark:opacity-40" />
                <div class="absolute inset-0 bg-gradient-to-t from-brand-blue-light/70 dark:from-neutral-950/90 via-white/80 dark:via-neutral-900/60 to-white/20"></div>
            </div>
            <div class="relative z-10 container mx-auto px-6 text-center">
                <h1 class="font-bebas text-[clamp(2.5rem,12vw,8rem)] leading-[0.85] mb-8 text-dark-text dark:text-neutral-100">O CAMPEÃO DO<br/><span class="text-brand-blue">CHURRASCO</span></h1>
                <p class="max-w-2xl mx-auto text-base md:text-2xl text-dark-text/70 dark:text-neutral-300 font-light mb-16">A tradição de Mogi Mirim em um ambiente feito para sua família.</p>
                <div class="flex flex-col items-center gap-4"><div class="h-20 w-[1px] bg-brand-blue"></div><span class="uppercase tracking-[0.4em] text-[10px] md:text-xs">Cardápio abaixo</span></div>
            </div>
        </section>

        <section id="menu" class="py-24 relative bg-white dark:bg-neutral-950">
            <div class="container mx-auto px-4">
                <div class="text-center mb-16">
                   <h2 class="font-bebas text-5xl md:text-8xl mb-10 text-dark-text dark:text-neutral-100 uppercase">Saboreie momentos em <span class="text-brand-blue">família.</span></h2>
                    <div class="flex flex-wrap justify-center gap-2 bg-brand-blue/5 p-2 rounded-xl max-w-4xl mx-auto mb-12">
                       {tabs_btns_html}
                    </div>
                </div>
                {tabs_content_html}
            </div>
        </section>

        <section id="location" class="py-32 bg-white dark:bg-neutral-950 overflow-hidden relative">
          <div class="container mx-auto px-6 relative z-10">
            <div class="flex flex-col lg:flex-row gap-20 items-center">
              <div class="w-full lg:w-1/2">
                <h2 class="font-bebas text-6xl md:text-8xl mb-8">ONDE A <span class="text-brand-blue">BRASA</span> VIVE</h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-12">
                   <div class="flex gap-5 items-start"><div class="p-4 bg-brand-blue/5 rounded-2xl"><svg class="w-6 h-6 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg></div><div><h4 class="font-bold uppercase text-[10px] tracking-[0.3em] mb-3">Endereço</h4><p class="text-sm">Av. 22 de Outubro, 630<br/>Mogi Mirim</p></div></div>
                   <div class="flex gap-5 items-start"><div class="p-4 bg-brand-blue/5 rounded-2xl"><svg class="w-6 h-6 text-brand-blue" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div><div><h4 class="font-bold uppercase text-[10px] tracking-[0.3em] mb-3">Horário</h4><p class="text-sm">Segunda a Sábado<br/>17:30 às 22:30</p></div></div>
                </div>
              </div>
              <div class="w-full lg:w-1/2 h-[500px] shadow-2xl rounded-3xl overflow-hidden">
                <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3686.299658249692!2d-46.96691642382121!3d-22.42566487401147!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x94c8f9006208546b%3A0xf1877d21099b3bd1!2sMogi%20Campe%C3%A3o%20do%20Churrasco%20-%2022%20de%20Outubro!5e0!3m2!1spt-BR!2sbr!4v1739316684000!5m2!1spt-BR!2sbr" width="100%" height="100%" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
              </div>
            </div>
          </div>
        </section>

        <footer class="bg-white dark:bg-neutral-900 border-t border-black/5 py-16 px-6 text-center">
           <div class="container mx-auto flex flex-col items-center gap-10">
              {logo_md}
              <div class="text-center">
                 <p class="font-bold uppercase tracking-[0.4em] mb-4">Aberto todos os dias</p>
                 <p class="text-dark-text/40 text-xs font-medium">Av. 22 de Outubro, 630 • Mogi Mirim<br/>© 2026</p>
              </div>
           </div>
        </footer>

        <script>
            function toggleDarkMode() {{
                const html = document.documentElement;
                if (html.classList.contains('dark')) {{
                    html.classList.remove('dark');
                    localStorage.setItem('theme', 'light');
                }} else {{
                    html.classList.add('dark');
                    localStorage.setItem('theme', 'dark');
                }}
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
                document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('bg-brand-blue', 'text-white'));
                document.getElementById('tab-content-' + id).classList.add('active');
                document.getElementById('tab-btn-' + id).classList.add('bg-brand-blue', 'text-white');
                filterSubCat('all');
            }}

            function filterSubCat(s) {{
                document.querySelectorAll('.subcat-btn').forEach(b => {{
                    if (b.innerText.toLowerCase() === s.toLowerCase() || (s === 'all' && b.innerText === 'Todos')) b.classList.add('bg-brand-blue', 'text-white');
                    else b.classList.remove('bg-brand-blue', 'text-white');
                }});
                document.querySelectorAll('.product-card').forEach(c => {{
                    c.style.display = (s === 'all' || c.getAttribute('data-subcat') === s) ? 'flex' : 'none';
                }});
                if (window.ScrollTrigger) ScrollTrigger.refresh();
            }}

            document.addEventListener("DOMContentLoaded", () => {{
                if (window.gsap) {{
                   gsap.registerPlugin(ScrollTrigger);
                   gsap.utils.toArray('.reveal-on-scroll').forEach(s => gsap.fromTo(s, {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 1, scrollTrigger: {{ trigger: s, start: 'top 90%' }} }}));
                }}
                updateAdminUI();
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
