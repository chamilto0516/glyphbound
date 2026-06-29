from __future__ import annotations

from typing import List

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from .items import Item, ItemKind, shop_stock
from .player import Player


class ShopScreen(Screen):
    CSS = """
    ShopScreen {
        background: rgba(0,0,0,0.85);
        align: center middle;
    }

    #shop-box {
        width: 58;
        height: auto;
        border: double ansi_bright_yellow;
        padding: 1 2;
        background: black;
    }

    #shop-title {
        text-align: center;
        text-style: bold;
        color: ansi_bright_yellow;
        margin-bottom: 1;
    }

    #shop-gold {
        color: yellow;
        margin-bottom: 1;
    }

    .shop-item {
        color: white;
    }

    .shop-item-selected {
        color: black;
        background: ansi_bright_yellow;
        text-style: bold;
    }

    #shop-status {
        color: #aaaaaa;
        margin-top: 1;
    }

    #shop-hint {
        color: #666666;
        margin-top: 0;
    }
    """

    def __init__(self, player: Player, floor: int) -> None:
        super().__init__()
        self.player = player
        self.floor = floor
        self._stock: List[Item] = []
        self._cursor = 0
        self._status = "Welcome! What can I get you?"

    def compose(self) -> ComposeResult:
        with Static(id="shop-box"):
            yield Static("$ Merchant's Stall $", id="shop-title")
            yield Static("", id="shop-gold")
            yield Static("", id="shop-items")
            yield Static("", id="shop-status")
            yield Static("↑↓ navigate   B/Enter buy   Esc leave", id="shop-hint")

    def on_mount(self) -> None:
        self._stock = shop_stock(self.floor)
        self._refresh_display()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)
            return
        if event.key in ("up", "k"):
            self._cursor = (self._cursor - 1) % len(self._stock)
            self._refresh_display()
        elif event.key in ("down", "j"):
            self._cursor = (self._cursor + 1) % len(self._stock)
            self._refresh_display()
        elif event.key in ("b", "enter"):
            self._do_buy()

    def _do_buy(self) -> None:
        item = self._stock[self._cursor]
        price = item.gold_value
        if self.player.gold >= price:
            self.player.gold -= price
            self.player.inventory.append(item)
            self.player.stat_items_found += 1
            self._status = f"[green]Bought {item.name} for {price} gp.[/green]"
        else:
            self._status = f"[red]Not enough gold — need {price} gp, you have {self.player.gold} gp.[/red]"
        self._refresh_display()

    def _refresh_display(self) -> None:
        self.query_one("#shop-gold", Static).update(
            f"Gold: [bold yellow]{self.player.gold} gp[/bold yellow]"
        )

        lines = []
        for i, item in enumerate(self._stock):
            price = item.gold_value
            affordable = self.player.gold >= price
            price_str = f"[yellow]{price} gp[/yellow]" if affordable else f"[dim]{price} gp[/dim]"
            label = _item_label(item)
            if i == self._cursor:
                lines.append(f"[bold reverse] ▶ {label:<32} {price:>5} gp [/bold reverse]")
            else:
                color = "white" if affordable else "dim"
                lines.append(f"[{color}]   {label:<32}[/{color}] {price_str}")

        self.query_one("#shop-items", Static).update("\n".join(lines))
        self.query_one("#shop-status", Static).update(self._status)


def _item_label(item: Item) -> str:
    """Short descriptive label for a shop item."""
    parts = [item.name]
    if item.attack_bonus:
        parts.append(f"+{item.attack_bonus} Atk")
    if item.defense_bonus:
        parts.append(f"+{item.defense_bonus} Def")
    if item.hp_bonus and item.kind == ItemKind.POTION:
        hp = "full" if item.hp_bonus >= 999 else f"+{item.hp_bonus}"
        parts.append(f"{hp} HP")
    if item.mp_bonus and item.kind == ItemKind.POTION:
        mp = "full" if item.mp_bonus >= 999 else f"+{item.mp_bonus}"
        parts.append(f"{mp} MP")
    if item.damage_sides:
        parts.append(f"{item.damage_count}d{item.damage_sides}")
    elif item.kind == ItemKind.SCROLL and item.hp_bonus:
        parts.append(f"+{item.hp_bonus} HP")
    return "  ".join(parts)
