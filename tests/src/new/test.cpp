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

int func(double a) {
   return 42;
}

int var = 17;

class Test1 {
   public:
      
      static int f(int a, int b);
      int g(float a, float b);
      
   protected:
      
      static int m_;
};

int Test1::f(int a, int b) { return 42; }
int Test1::g(float a, float b) { return 1; }

int Test1::m_ = 13;

int persisting1(int a) { return 42; }
int persisting2(int a) { return 42; }
