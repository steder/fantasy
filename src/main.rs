extern crate postgres;

#![feature(phase)]

#[phase(syntax)]
extern crate postgres_macros;

use postgres;


fn main() {
    println!("Hello, world!")
}
