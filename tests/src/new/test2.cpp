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

double fIStay(double a) { return a; }
char fIStayButDiffer(char a) { return a; }
short fIAmNew(short a) { return a; }

int vIStay = 18;
int vIStayButDiffer = 59;
int vIAmNew = 20;

const int cIStay = 28;
const int cIStayButDiffer = 69;
const int cIAmNew = 30;

void g() {
  static int lsvIStay = 38;
  static int lsvIStayButDiffer = 79;
  static int lsvIAmNew = 40;
}

class Test {
  public:
      
    double mIStay(double a) { return a; }
    char mIStayButDiffer(char a) { return a; }
    short mIAmNew(short a) { return a; }

    static double smIStay(double a) { return a; }
    static char smIStayButDiffer(char a) { return a; }
    static short smIAmNew(short a) { return a; }
      
  private:

    int mvIStay = 18;
    int mvIStayButDiffer = 49;
    int mvIAmNew = 20;
      
    static int smvIStay;
    static int smvIStayButDiffer;
    static int smvIAmNew;
};

int Test::smvIStay = 28;
int Test::smvIStayButDiffer = 69;
int Test::smvIAmNew = 30;

struct IStay { void f() {} };
struct IStayButDiffer { void g() {} };
struct IAmNew { void f() {} };

int implementationChanged(int a) {
  int b = 3*a + 3;
  for(int i = 0; i < a; ++i) {
    b = (b - i) % 15;
  }
  b = b + 1;
  return b;
}
