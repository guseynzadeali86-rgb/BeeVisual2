package dev.beevisual.setting;

import java.util.Locale;

public final class Setting {
    public enum Type { BOOL, NUMBER, MODE }

    public final String name;
    public final Type type;
    public boolean bool;
    public double value;
    public double min;
    public double max;
    public double step;
    public final String[] modes;
    public int index;

    private Setting(String name, Type type, String[] modes) {
        this.name = name;
        this.type = type;
        this.modes = modes;
    }

    public static Setting ofBool(String name, boolean def) {
        Setting s = new Setting(name, Type.BOOL, null);
        s.bool = def;
        return s;
    }

    public static Setting ofNumber(String name, double def, double min, double max, double step) {
        Setting s = new Setting(name, Type.NUMBER, null);
        s.value = def;
        s.min = min;
        s.max = max;
        s.step = step;
        return s;
    }

    public static Setting ofMode(String name, int def, String... modes) {
        Setting s = new Setting(name, Type.MODE, modes);
        s.index = def;
        return s;
    }

    public boolean getBool() { return bool; }
    public double getNum() { return value; }
    public int getInt() { return (int) Math.round(value); }
    public int getIndex() { return index; }

    public void next(int dir) {
        if (modes == null || modes.length == 0) return;
        index = ((index + dir) % modes.length + modes.length) % modes.length;
    }

    public String display() {
        switch (type) {
            case BOOL:
                return bool ? "вкл" : "выкл";
            case NUMBER:
                return step >= 1 ? String.valueOf((int) Math.round(value)) : String.format(Locale.ROOT, "%.1f", value);
            default:
                return modes[index];
        }
    }
}
