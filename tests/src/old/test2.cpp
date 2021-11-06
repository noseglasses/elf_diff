// -*- mode: c++ -*-
//
// elf_diff
//
// Copyright (C) 2019  Noseglasses (shinynoseglasses@gmail.com)
//
// This program is free software: you can redistribute it and/or modify it under
// the terms of the GNU General Public License as published by the Free Software
// Foundation, version 3.
//
// This program is distributed in the hope that it will be useful, but WITHOUT but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
// FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
// details.
//
// You should have received a copy of the GNU General Public License along with along with
// this program. If not, see <http://www.gnu.org/licenses/>.
//

int fIAmGone(int a) { return a; }
double fIStay(double a) { return a; }
float fIStayButDiffer(float a) { return a; }

int vIAmGone = 17;
int vIStay = 18;
int vIStayButDiffer = 19;

const int cIAmGone = 27;
const int cIStay = 28;
const int cIStayButDiffer = 29;

void g() {
  static int lsvIAmGone = 37;
  static int lsvIStay = 38;
  static int lsvIStayButDiffer = 39;
}

class Test {
  public:
      
    int mIAmGone(int a) { return a; }
    double mIStay(double a) { return a; }
    float mIStayButDiffer(float a) { return a; }

    static int smIAmGone(int a) { return a; }
    static double smIStay(double a) { return a; }
    static float smIStayButDiffer(float a) { return a; }
      
  private:

    int mvIAmGone = 17;
    int mvIStay = 18;
    int mvIStayButDiffer = 19;
      
    static int smvIAmGone;
    static int smvIStay;
    static int smvIStayButDiffer;
};

int Test::smvIAmGone = 27;
int Test::smvIStay = 28;
int Test::smvIStayButDiffer = 29;

struct IAmGone { void f() {} };
struct IStay { void f() {} };
struct IStayButDiffer { void f() {} };

int implementationChanged(int a) {
  int b = 2*a + 3;
  for(int i = 0; i < a; ++i) {
    b = (b + i) % 17;
  }
  return b;
}
