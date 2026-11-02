# 🤖 Promo Resina Bot — agente de promoções de resina 3D (AliExpress → WhatsApp)

Agente que procura promoções de **resina para impressora 3D** no AliExpress, gera o **link de afiliado**
(você ganha comissão), cria uma **arte** no estilo dos canais de promoção e **posta no seu grupo/canal do WhatsApp**.
A ideia é a mesma de canais como o Nintendo Barato.

```
AliExpress Affiliate API ──► filtros (resina 3D, desconto, avaliação, preço) ──► anti-repetição (SQLite)
        ──► arte 1000x900 + legenda ──► WhatsApp (Evolution API) ──► grupos / canal
```

Exemplo de legenda gerada:

~~~
🔥 *ELEGOO Resina Padrão 8K 1kg Lavável em Água Cinza Impressora 3D LCD…*

_Resina super bem avaliada (98% positivas) com 44% de desconto._

🎟️ *Use o cupom:*
```RESINA10```

- *Preço:* R$89,90 ~R$159,90~ (44% OFF)
- *Loja:* AliExpress

- *Link de compra:* https://s.click.aliexpress.com/e/...

*Entre nos Grupos*
https://chat.whatsapp.com/...
~~~

## ⚡ Instalação rápida (checklist)

**O que só você pode fazer (precisa do seu login):**
- [ ] Cadastro de afiliado em <https://portals.aliexpress.com> e criação do Tracking ID (Ferramentas → Tracking ID)
- [ ] Criação de um app da categoria **Affiliates** em <https://openservice.aliexpress.com>, e esperar a aprovação
- [ ] Um chip/número de WhatsApp só para o bot, e esse número como **admin** do grupo/canal

**O resto é automático:**
```bash
python -m promobot configurar      # pergunta as chaves, cria o .env e testa a API
docker compose up -d               # sobe o WhatsApp (Evolution API) + o agente
```
Abra `http://SEU_SERVIDOR:8080/manager` e entre com a `EVOLUTION_API_KEY` que está no `.env`.
Crie a instância `promo` e leia o QR code com o celular do bot. Depois rode
`docker compose run --rm promobot python -m promobot grupos`, copie os IDs para `WHATSAPP_TARGETS`,
mude `WHATSAPP_PROVIDER=evolution` e rode `docker compose up -d` de novo.

## 1. Pré-requisitos

1. **Conta de afiliado AliExpress**: cadastre-se em <https://portals.aliexpress.com> e crie um *Tracking ID*.
2. **App na AliExpress Open Platform**: em <https://openservice.aliexpress.com>, crie um app do tipo
   *Affiliate* e copie o `App Key` e o `App Secret` (a aprovação leva alguns dias).
3. **Evolution API** (ponte com o WhatsApp). Com Docker:
   ```bash
   docker run -d --name evolution -p 8080:8080 \
     -e AUTHENTICATION_API_KEY=minha-chave-secreta \
     atendai/evolution-api:latest
   ```
   Depois crie uma instância e leia o QR code com o WhatsApp do número que vai postar
   (pelo painel em `http://localhost:8080/manager` ou pela API `POST /instance/create`).
   **Use um número separado (chip só para o canal)**, não o seu pessoal.
4. Python 3.10+.

## 2. Instalação

```bash
cd promo-resina-bot
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # preencha suas chaves
```

### Identidade visual (Forja Nerd)

Coloque suas artes em `assets/`:

| Arquivo | Uso |
|---|---|
| `assets/moldura.png` | **Arte pronta da marca** (faixas, logo, redes sociais). O agente cola a foto do produto, o preço e o selo de desconto dentro dela, como o Nintendo Barato faz. |
| `assets/logo.png` | Logo no canto da faixa (só é usado quando não há moldura) |
| `assets/fonte.ttf` | Fonte da marca para preço e textos |

Use `CARD_PHOTO_BOX=x1,y1,x2,y2` no `.env` para dizer em que área da moldura a foto entra. Use `CARD_SHOW_PRICE=false`
se a sua arte não tiver espaço para o preço. Cor, nome, site e hashtag ficam em `BRAND_*`.

## 3. Uso

```bash
python -m promobot demo          # gera um post de exemplo em output/ (não precisa de chaves)
python -m promobot grupos        # lista os IDs dos seus grupos (ex: 1203630...@g.us)
python -m promobot run           # busca e posta as melhores promoções agora
python -m promobot loop          # fica rodando e posta a cada INTERVAL_MINUTES
python -m promobot link "https://pt.aliexpress.com/item/1005006123456789.html" --cupom BRASIL10
                                 # posta um achado seu, já com link de afiliado
python -m promobot link "https://s.click.aliexpress.com/e/_c3cDJ83V" --preco 79.90 --preco-antigo 139.90
                                 # sem API: título e fotos são lidos da página do anúncio
```

### Fotos do anúncio

O agente usa as fotos do próprio anúncio. Com a API, elas vêm da galeria do produto. Sem a API, ele lê a
página do link. A primeira foto vai em destaque na arte e até 3 outras aparecem como miniaturas
(`CARD_THUMBS`). Com `EXTRA_PHOTOS=2`, ele também envia 2 fotos extras do anúncio logo depois do post.

Comece com `WHATSAPP_PROVIDER=dryrun`: ele só salva arte + legenda em `output/` para você conferir.
Quando estiver bom, mude para `evolution` e coloque os destinos em `WHATSAPP_TARGETS`.

## 4. Configuração (`.env`)

| Variável | O que faz |
|---|---|
| `SEARCH_KEYWORDS` | Termos de busca (resina 3d, resina lavável, marcas…) |
| `MAX_PRICE_BRL`, `MIN_DISCOUNT`, `MIN_RATING`, `MIN_SALES` | Filtros de qualidade da promoção |
| `POSTS_PER_RUN` | Quantas promoções por rodada |
| `REPOST_AFTER_DAYS` | Não repete o mesmo produto antes disso (a menos que o preço caia 5%+) |
| `WHATSAPP_TARGETS` | Grupos (`...@g.us`) e/ou canal (`...@newsletter`), separados por vírgula |
| `BRAND_*`, `GROUPS_LINK` | Nome, site, hashtag e cor da sua marca na arte e na legenda |
| `USE_AI_COPY` | `true` para o Claude escrever a frase de destaque de cada produto (precisa de `ANTHROPIC_API_KEY`) |
| `QUIET_HOURS` | Faixa sem posts (ex.: `23-8`) |

O filtro só deixa passar títulos com "resina/resin" **e** um termo de impressão 3D (3D, UV, 405nm, LCD,
marcas como Elegoo, Anycubic, Sunlu…) e descarta resina epóxi/artesanato. Ajuste em `promobot/selector.py`.

## 5. Grupo ou Canal?

- **Grupo "somente admins"** (como no print do Nintendo Barato): funciona com a Evolution API. O número do bot
  precisa ser **admin** do grupo. Grupos têm limite de membros, por isso esses canais usam vários (#1, #2…, #28):
  coloque todos em `WHATSAPP_TARGETS`.
- **Canal do WhatsApp**: a Evolution API v2 (Baileys) consegue enviar para o ID `...@newsletter` do canal se o
  número do bot for administrador. É uma função mais nova e menos estável, então teste antes.
- A **API oficial da Meta (Cloud API)** não posta em canais e é feita para mensagens 1-para-1, então não serve aqui.

## 6. Rodando 24h

- **VPS barata** (Oracle Free Tier, Contabo, Hetzner…) com Docker para a Evolution API e
  `python -m promobot loop` dentro de um `tmux`/`systemd`.
- Ou use o cron: `0 9-22/2 * * * cd /caminho/promo-resina-bot && .venv/bin/python -m promobot run`

## ⚠️ Cuidados

- A Evolution API usa o WhatsApp Web (não é oficial). Poste em ritmo humano (o padrão é poucos posts a cada 2h)
  e use um chip dedicado para reduzir o risco de banimento.
- Avise na descrição do canal que os links são de afiliado. É transparente e é o que as regras do programa pedem.
- Preços do AliExpress mudam rápido. A legenda já inclui "preço sujeito a alteração".
