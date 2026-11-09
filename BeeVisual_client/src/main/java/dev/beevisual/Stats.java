package dev.beevisual;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;

/** Shared runtime statistics used by several HUD modules. */
public final class Stats {
    public static double speed;            // blocks per second
    public static int deaths;
    public static int kills;
    public static long sessionStart = System.currentTimeMillis();
    public static LivingEntity target;
    public static long lastHit;

    private static double lastX = Double.NaN;
    private static double lastZ = Double.NaN;
    private static boolean wasDead;
    private static boolean killCounted;

    private Stats() {}

    public static void tick(MinecraftClient mc) {
        ClientPlayerEntity p = mc.player;
        if (p == null) {
            lastX = Double.NaN;
            lastZ = Double.NaN;
            speed = 0;
            return;
        }
        if (!Double.isNaN(lastX)) {
            double dx = p.getX() - lastX;
            double dz = p.getZ() - lastZ;
            double inst = Math.sqrt(dx * dx + dz * dz) * 20.0;
            speed = speed * 0.7 + inst * 0.3;
        }
        lastX = p.getX();
        lastZ = p.getZ();

        boolean dead = p.isDead() || p.getHealth() <= 0;
        if (dead && !wasDead) deaths++;
        wasDead = dead;

        long now = System.currentTimeMillis();
        if (target != null) {
            if (!killCounted && (target.isDead() || target.getHealth() <= 0) && now - lastHit < 10000) {
                kills++;
                killCounted = true;
            }
            if (now - lastHit > 15000) target = null;
        }
    }

    public static void onAttack(Entity e) {
        if (e instanceof LivingEntity le) {
            if (le != target) killCounted = false;
            target = le;
            lastHit = System.currentTimeMillis();
        }
    }

    public static void reset() {
        sessionStart = System.currentTimeMillis();
        deaths = 0;
        kills = 0;
        target = null;
    }
}
