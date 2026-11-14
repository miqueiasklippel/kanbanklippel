<p align="center">
  <img src="icon.png" alt="Kanban Klippel" width="128">
</p>

<h1 align="center">Kanban Klippel</h1>

<p align="center">
  Quadro kanban 100% offline, com cofres criptografados salvos no computador ou em uma nuvem WebDAV.
</p>

---

## Sobre

O **Kanban Klippel** é um aplicativo de quadros kanban para organizar tarefas e projetos. Todo o aplicativo é um único arquivo HTML, sem dependências externas, que funciona tanto no navegador quanto como aplicativo de desktop para Linux (Flatpak, GTK 4 + WebKit).

## Recursos

- **Totalmente offline** — nenhum servidor, nenhuma conta, nenhum rastreamento.
- **Cofres criptografados** — a chave é derivada por PBKDF2-SHA256 (210.000 iterações) e o conteúdo é cifrado com AES-GCM de 256 bits.
- **Sincronização via WebDAV** — salve seus cofres no Nextcloud, ownCloud ou qualquer servidor WebDAV.
- **Arrastar e soltar** cartões entre colunas.
- **Prazos**, atalhos de teclado e tema claro/escuro.
- **Arquivo único** — fácil de auditar, copiar e levar com você.

## Como usar

### No navegador

Abra o arquivo `index.html` em qualquer navegador moderno. Pronto.

### Como aplicativo Flatpak (Linux)

Requisitos: `flatpak` instalado.

```bash
cd flatpak
./build.sh --install
flatpak run io.github.miqueiasklippel.KanbanKlippel
```

O script instala os runtimes necessários do Flathub (GNOME 50), compila o aplicativo e gera o pacote `kanban-klippel-1.0.0.flatpak`. Sem `--install`, apenas gera o pacote.

## Estrutura do projeto

```
.
├── index.html                # O aplicativo inteiro (HTML + CSS + JS)
├── icon.png                  # Ícone
└── flatpak/
    ├── build.sh              # Script de build do Flatpak
    ├── kanban-klippel.py     # Janela GTK 4 / WebKit que carrega o index.html
    ├── bridge.js             # Ponte entre a página e o app nativo
    ├── icons/                # Ícones em 64, 128, 256 e 512 px
    └── io.github.miqueiasklippel.KanbanKlippel.*  # Manifesto, .desktop e metainfo
```

## Licença

Este projeto é distribuído sob a **[PolyForm Noncommercial License 1.0.0](LICENSE)**.

O código é aberto: você pode usar, estudar, modificar e redistribuir livremente para **fins não comerciais** (uso pessoal, estudo, pesquisa, organizações sem fins lucrativos, instituições de ensino e órgãos públicos).

**Uso comercial não é permitido** sem autorização prévia do autor. Para licenciamento comercial, entre em contato pelo GitHub.

Copyright © 2026 Miqueias Klippel
