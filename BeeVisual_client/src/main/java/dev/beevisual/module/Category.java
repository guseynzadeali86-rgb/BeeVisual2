package dev.beevisual.module;

public enum Category {
    HUD("HUD"),
    RENDER("Рендер"),
    WORLD("Мир");

    public final String title;

    Category(String title) {
        this.title = title;
    }
}
