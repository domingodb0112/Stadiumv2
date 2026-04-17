package com.stadiumv2;

public class PlayerData {
    public final int id;
    public final String name;
    public final int drawableRes;
    public final String videoFile;
    public boolean selected = false;

    public PlayerData(int id, String name, int drawableRes, String videoFile) {
        this.id = id;
        this.name = name;
        this.drawableRes = drawableRes;
        this.videoFile = videoFile;
    }

    public static PlayerData[] getAll() {
        return new PlayerData[]{
            new PlayerData(0, "Edson Álvarez",  R.drawable.edson_alvarez_gm,    "edsonAlvarez.mov"),
            new PlayerData(1, "Gilberto Mora",   R.drawable.gilberto_mora_gm,    "gilbertoMora.mov"),
            new PlayerData(2, "Jorge Sánchez",   R.drawable.jorge_sanchez_gm,    "jorgeSanchez.mov"),
            new PlayerData(3, "Mateo Chávez",    R.drawable.mateo_chavez_gm,     "mateoChavez.mov"),
            new PlayerData(4, "Raúl Jiménez",    R.drawable.raul_jimenez_gm,     "raulJimenez.mov"),
            new PlayerData(5, "Raúl Rangel",     R.drawable.raul_rangel_gm,      "raulRangel.mov"),
        };
    }
}
